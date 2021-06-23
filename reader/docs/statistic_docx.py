from django.conf import settings
from django.core.files import File
from docx import Document
from docx.enum.section import WD_ORIENTATION
from datetime import datetime

from accountBd.models import Profile, User, FileRepository


def journal(document_name):
    """
    Функция для создания шаблона документа для инструктожа

    :return: Шаблон документа для инструктажа
    """

    document = Document()

    # Для альбомногй ориентации
    section = document.sections[-1]
    new_width, new_height = section.page_height, section.page_width
    section.orientation = WD_ORIENTATION.LANDSCAPE
    section.page_width = new_width
    section.page_height = new_height
    document.add_heading('Список личного состава', 0)

    table = document.add_table(rows=1, cols=7)
    table.style = 'Table Grid'

    c = table.rows[0].cells
    c[0].text = 'Дата'
    c[1].text = 'Должность и звание'
    c[2].text = 'ФИО'
    c[3].text = 'Вид инструктажа'
    c[4].text = 'Подпись инструктирующего'
    c[5].text = 'Подпись инструктируемого'
    c[6].text = 'Примечание'

    document.save(f'media/docs/{document_name}')


def event_statistic(list_user, document_name):
    """
    Функция для внесения записей в журнал

    :param list_user: Список с пользователями
    :param document_name: Название файла
    :return: Добавляет список пользоваетелй в таблицу, которая создается в функции journal()
    """

    document = Document(f'media/docs/{document_name}')

    for user in list_user:
        table = document.add_table(rows=1, cols=7)
        table.style = 'Table Grid'
        c = table.rows[0].cells
        c[0].text = f'{user[0]}'
        c[1].text = f'{user[1]}\n{user[2]}'
        c[2].text = f'{user[3]}'
        c[3].text = 'целевой'
        c[4].text = ''
        c[5].text = ''
        c[6].text = ''

    document.save(f'media/docs/{document_name}')


def user_statistic(time_schedule, time_work, real_overtime, time_of_respectful_absence_plan,
                   time_of_respectful_absence_fact, time_of_not_respectful_absence_fact,
                   percent_time_work, percent_time_of_respectful_absence, percent_time_of_not_respectful_absence,
                   position, rank, name, project, document_name):
    document = Document(f'media/docs/{document_name}')
    document.add_paragraph(f'Отчет по деятельности: {str(position).lower()} {str(rank).lower()} {name}\n\n',
                           style='Heading 1')

    table = document.add_table(rows=1, cols=2)

    table.style = 'Medium List 1 Accent 1'

    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Название показателя'
    hdr_cells[1].text = 'Данные'

    row_cells = table.add_row().cells
    row_cells[0].text = 'Время работы по плану '
    row_cells[1].text = str(time_schedule)

    row_cells = table.add_row().cells
    row_cells[0].text = 'Время фактической работы '
    row_cells[1].text = str(time_work)

    row_cells = table.add_row().cells
    row_cells[0].text = 'Время фактической переработки '
    row_cells[1].text = str(real_overtime)

    row_cells = table.add_row().cells
    row_cells[0].text = 'Время фактических уважительных прогулов '
    row_cells[1].text = str(time_of_respectful_absence_fact)

    row_cells = table.add_row().cells
    row_cells[0].text = 'Время фактических не уважительных прогулов '
    row_cells[1].text = str(time_of_not_respectful_absence_fact)

    row_cells = table.add_row().cells
    row_cells[0].text = 'Процент фактической работы в общем количестве времени '
    row_cells[1].text = str(percent_time_work)

    row_cells = table.add_row().cells
    row_cells[0].text = 'Процент уважительных прогулов в общем количестве времени '
    row_cells[1].text = str(percent_time_of_respectful_absence)

    row_cells = table.add_row().cells
    row_cells[0].text = 'Процент не уважительных прогулов в общем количестве времени '
    row_cells[1].text = str(percent_time_of_not_respectful_absence)

    document.add_paragraph(f'\n\n{position} {name} находится на проекте {project}')

    # Разрыв старницы
    document.add_page_break()

    document.save(f'media/docs/{document_name}')


# Функция для получения docx файла по одному пользователю
def user_statistic_report(serializer, user_id, document_name):
    document = Document()
    document.save(f'media/docs/{document_name}')

    user_statistic(
        serializer['time_schedule'],
        serializer['time_work'],
        serializer['real_overtime'],
        serializer['time_of_respectful_absence_plan'],
        serializer['time_of_respectful_absence_fact'],
        serializer['time_of_not_respectful_absence_fact'],
        serializer['percent_time_work'],
        serializer['percent_time_of_respectful_absence'],
        serializer['percent_time_of_not_respectful_absence'],
        Profile.objects.get(user_id=user_id).get_position_display(),
        Profile.objects.get(user_id=user_id).get_rank_display(),
        User.objects.get(id=user_id).get_full_name(),
        serializer['project'], document_name
    )


# Функция для получения docx файла по всем пользователям
def users_statistic_report(queryset, document_name):
    document = Document()
    document.save(f'media/docs/{document_name}')
    profiles = list(queryset)

    for profile in profiles:
        user_statistic(
            profile.time_schedule,
            profile.time_work,
            profile.real_overtime,
            profile.time_of_respectful_absence_plan,
            profile.time_of_respectful_absence_fact,
            profile.time_of_not_respectful_absence_fact,
            profile.time_work / profile.time_schedule * 100,
            profile.time_of_respectful_absence_fact / profile.time_schedule * 100,
            profile.time_of_not_respectful_absence_fact / profile.time_schedule * 100,
            profile.get_position_display(),
            profile.get_rank_display(),
            profile.user.get_full_name(),
            profile.project,
            document_name
        )
