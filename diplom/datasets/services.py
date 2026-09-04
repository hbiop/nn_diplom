import pandas as pd

from .models import DataFile


def create_dataset(*, form, user):
    data_file = form.save(commit=False)
    data_file.user = user
    data_file.save()
    return data_file


def delete_dataset(data_file):
    file_field = data_file.file
    data_file.delete()
    if file_field:
        file_field.delete(save=False)


def read_dataset_preview(data_file, limit=100):
    if data_file.file_type == 'CSV':
        dataframe = pd.read_csv(data_file.file.path)
    elif data_file.file_type == 'XLSX':
        dataframe = pd.read_excel(data_file.file.path)
    else:
        raise ValueError(f'Неподдерживаемый тип файла: {data_file.file_type}')

    return {
        'columns': dataframe.columns.tolist(),
        'rows': dataframe.to_dict('records')[:limit],
    }
