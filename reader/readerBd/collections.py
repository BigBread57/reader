import datetime


class TypeOfDay:
    """
    Класс содержит константы, которые характеризуют тип дня. Тип дня Work определяеь рабочий день. Во время него могут
    происходить другие уважительные и не уважиетльные события, которые описаны в классе ListEvents приложения readerBd.
    """

    WORK = 'work'
    DUTY = 'duty'
    HOSPITAL = 'hospital'
    BUSINESS_TRIP = 'business_trip'
    OUTPUT = 'output'
    STATUS_CHOICES = [
        (WORK, 'Рабочий день'),
        (DUTY, 'Наряд'),
        (HOSPITAL, 'Госпиталь'),
        (BUSINESS_TRIP, 'Командировка'),
        (OUTPUT, 'Выходной'),
    ]


class Times:
    """
    Класс предназначе дня хранения временных значений, которые хараткреизуют расписание рабочего дня, начало, обеденный
    перерыв, уход домой. График работы делится для на график для персонала и для операторов.
    """

    TIME_ENTRY_MORNING_OPERATOR = datetime.time(hour=6)
    TIME_EXIT_MORNING_OPERATOR = datetime.time(hour=10)
    TIME_ENTRY_EVENING_OPERATOR = datetime.time(hour=12)
    TIME_EXIT_EVENING_OPERATOR = datetime.time(hour=14)

    TIME_ENTRY_MORNING_PERSONAL = datetime.time(hour=6)
    TIME_EXIT_MORNING_PERSONAL = datetime.time(hour=10)
    TIME_ENTRY_EVENING_PERSONAL = datetime.time(hour=11)
    TIME_EXIT_EVENING_PERSONAL = datetime.time(hour=15)

    # Рабочее время до обеда и после обеда у персоанала
    TIME_WORK_OPERATOR = datetime.timedelta(hours=6)
    TIME_WORK_PERSONAL = datetime.timedelta(hours=8)

    TIME_END_WORK_DAY = datetime.time(hour=23, minute=59)
    TIME_DELAY = datetime.timedelta(minutes=10)
