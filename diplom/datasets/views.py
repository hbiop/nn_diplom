import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import DataFileForm
from .models import DataFile


def upload_dataset(request):
    if request.method == 'POST':
        form = DataFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                data_file = form.save()

                file_path = data_file.file.path
                if data_file.file_type == 'CSV':
                    df = pd.read_csv(file_path)
                elif data_file.file_type == 'XLSX':
                    df = pd.read_excel(file_path)

                messages.success(request, 'Файл успешно загружен и обработан')
                return redirect('dataset_detail', pk=data_file.pk)

            except Exception as e:
                messages.error(request, f'Ошибка обработки файла: {str(e)}')
    else:
        form = DataFileForm()

    return render(request, 'datasets/upload.html', {'form': form})


def delete_file(request, id):
    file = get_object_or_404(DataFile, pk=id)
    file.delete()
    return redirect('dataset_list')

def dataset_detail(request, pk):
    data_file = DataFile.objects.get(pk=pk)
    try:
        # Чтение данных для отображения
        if data_file.file_type == 'CSV':
            df = pd.read_csv(data_file.file.path)
        elif data_file.file_type == 'XLSX':
            df = pd.read_excel(data_file.file.path)

        context = {
            'data_file': data_file,
            'columns': df.columns.tolist(),
            'rows': df.to_dict('records')[:100],  # Первые 100 строк
        }
    except Exception as e:
        messages.error(request, f'Ошибка чтения файла: {str(e)}')
        context = {'data_file': data_file}

    return render(request, 'datasets/detail.html', context)

def dataset_list(request):
    datasets = DataFile.objects.all().order_by('-upload_date')
    return render(request, 'datasets/list.html', {'datasets': datasets})