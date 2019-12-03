import json
import argparse
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sqlalchemy import create_engine


# Credit https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


with open('growthplot_config.json', 'r') as file:
    CONFIG = json.load(file)

with open(resource_path('resources/cdc_charts.json'), 'r') as file:
    PERCENTILE_DATA = json.load(file)


def query_db(patient_id: int):
    engine = create_engine(
        'mysql+mysqlconnector://{username}:{password}@{server}/{database}'.
        format(**CONFIG))

    sql = '''
        SELECT visit.PatientID,
               CONCAT(id.GivenName, ' ', id.FamilyName) as Name,
               id.Gender, id.Birthdate, visit.Weight, visit.Length,
               visit.HeadCirc, visit.VisitDate
        FROM visit
        LEFT JOIN id ON visit.PatientID = id.IDnumber
        WHERE visit.PatientID={}
    '''.strip()

    # Perform SQL query
    data_df = pd.read_sql_query(sql.format(patient_id), engine)

    # Get age in days
    data_df['Age'] = (data_df.VisitDate - data_df.Birthdate)

    # Approximate age in months
    data_df.Age = data_df.Age.dt.days / 30

    return data_df


def make_subplot(ax, data_df: pd.DataFrame, what: str):
    gender = 'male' if data_df['Gender'].iloc[0] == 'M' else 'female'
    percentile_df = pd.DataFrame(PERCENTILE_DATA[what][gender])

    # Plot percentile lines
    x = 'length' if what == 'weight-for-length' else 'age'
    percentile_df.plot(
        x=x, y=['3', '50', '97'], ax=ax,
        kind='line', color='gray', linewidth='1'
    )
    percentile_df.plot(
        x=x, y=['5', '10', '25', '75', '90', '95'], ax=ax,
        kind='line', color='gray', linewidth='0.5'
    )

    if what == 'length-for-age':
        x = 'Age'
        y = 'Length'
        x_label = 'Age (in months)'
        y_label = 'Length (in centimeters)'
        x_ticks = np.arange(0, 37, 2)
        x_ticks_minor = np.arange(0, 37, 1)
        y_ticks = np.arange(40, 110, 5)
        y_ticks_minor = np.arange(40, 110, 2.5)
        percentile_label_position = 36
    elif what == 'weight-for-age':
        x = 'Age'
        y = 'Weight'
        x_label = 'Age (in months)'
        y_label = 'Weight (in kilograms)'
        x_ticks = np.arange(0, 37, 2)
        x_ticks_minor = np.arange(0, 37, 1)
        y_ticks = np.arange(0, 21, 1)
        y_ticks_minor = [0]
        percentile_label_position = 36
    elif what == 'head-circumference-for-age':
        x = 'Age'
        y = 'HeadCirc'
        x_label = 'Age (in months)'
        y_label = 'Head Circumference (in centimeters)'
        x_ticks = np.arange(0, 37, 2)
        x_ticks_minor = np.arange(0, 37, 1)
        y_ticks = np.arange(28, 56, 2)
        y_ticks_minor = np.arange(28, 56, 1)
        percentile_label_position = 36
    elif what == 'weight-for-length':
        x = 'Length'
        y = 'Weight'
        x_label = 'Length (in centimeters)'
        y_label = 'Weight (in kilograms)'
        x_ticks = np.arange(45, 103.5, 5)
        x_ticks_minor = np.arange(45, 103.5, 1)
        y_ticks = np.arange(0, 21, 1)
        y_ticks_minor = [0]
        percentile_label_position = 103.5

    # Plot patient data
    data_df.plot(
        x=x, y=y, ax=ax,
        kind='line', marker='o', linestyle='--',
        color='black', linewidth='1.5'
    )

    # Add labels
    ax.set_title(f'{data_df.Name.iloc[0]} {what}', color='black', fontsize=18)
    ax.set_ylabel(y_label, color='black', fontsize=16)
    ax.set_xlabel(x_label, color='black', fontsize=16)

    # Remove the automatically generated legend
    ax.legend().remove()

    # Add percentile label to each line
    last_vals = percentile_df.iloc[-1, 1:]
    for col, val in last_vals.items():
        if col not in ('5', '95'):
            ax.annotate(xy=(percentile_label_position, val),
                        s=str(col), color='gray')

    # Set color
    ax.patch.set_facecolor('white')
    ax.patch.set_edgecolor('white')
    ax.spines['bottom'].set_color('black')
    ax.spines['left'].set_color('black')
    ax.tick_params(axis='both', colors='black', labelsize=12)

    # Set grid interval
    ax.set_xticks(x_ticks)
    ax.set_xticks(x_ticks_minor, minor=True)
    ax.set_yticks(y_ticks)
    ax.set_yticks(y_ticks_minor, minor=True)

    ax.grid(which='major', linewidth='0.5', linestyle='-', color='black')
    ax.grid(which='minor', linewidth='0.5', linestyle=':', color='black')


def main():
    parser = argparse.ArgumentParser(description='''
        Generate a set of growth charts for an infant.
    ''')
    parser.add_argument('id', type=int, nargs=1, help='Database ID of patient')
    patient_id = parser.parse_args().id[0]

    patient_data = query_db(patient_id)

    with PdfPages('TEMP.pdf') as pdf:
        fig, axes = plt.subplots(2, 1, figsize=(8.5, 11))

        if patient_data.Length.any():
            make_subplot(ax=axes[0],
                         data_df=patient_data.query('Length > 0'),
                         what='length-for-age')

        if patient_data.Weight.any():
            make_subplot(ax=axes[1],
                         data_df=patient_data.query('Weight > 0'),
                         what='weight-for-age')

        fig.tight_layout()
        pdf.savefig(facecolor='white', papertype='letter',
                    bbox_inches='tight', pad_inches=0.75)
        plt.close()

        fig, axes = plt.subplots(2, 1, figsize=(8.5, 11))

        if patient_data.HeadCirc.any():
            make_subplot(ax=axes[0],
                         data_df=patient_data.query('HeadCirc > 0'),
                         what='head-circumference-for-age')

        if patient_data.Weight.any() and patient_data.Length.any():
            make_subplot(ax=axes[1],
                         data_df=patient_data.query(
                             'Weight > 0 and Length > 0'),
                         what='weight-for-length')

        fig.tight_layout()
        pdf.savefig(facecolor='white', papertype='letter',
                    bbox_inches='tight', pad_inches=0.75)
        plt.close()

    os.system('TEMP.pdf')


if __name__ == '__main__':
    main()
