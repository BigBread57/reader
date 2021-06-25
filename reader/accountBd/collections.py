class UserRank:
    """
    Класс, который содерит воинские звания
    """

    PRIVATE = 'private'
    LANCE_CORPORAL = 'lance_corporal'
    LANCE_SERGEANT = 'lance_sergeant'
    SERGEANT = 'sergeant'
    STAFF_SERGEANT = 'staff_sergeant'
    ENSIGN = 'ensign'
    STAFF_ENSIGN = 'staff_ensign'
    LIEUTENENT = 'lieutenant'
    STAFF_LIEUTENENT = 'staff_lieutenant'
    CAPTAIN = 'captain'
    MAJOR = 'major'
    LIEUTENENT_COLONEL = 'lieutenant colonel'
    COLONEL = 'colonel'
    GENERAL = 'general'

    STATUS_CHOICES = [
        (PRIVATE, 'Рядовой'),
        (LANCE_CORPORAL, 'Ефрейтор'),
        (LANCE_SERGEANT, 'Младший сержант'),
        (SERGEANT, 'Сержант'),
        (STAFF_SERGEANT, 'Старший сержант'),
        (ENSIGN, 'Прапорщик'),
        (STAFF_ENSIGN, 'Старший прапорщий'),
        (LIEUTENENT, 'Лейтенант'),
        (STAFF_LIEUTENENT, 'Старший лейтенант'),
        (CAPTAIN, 'Капитан'),
        (MAJOR, 'Майор'),
        (LIEUTENENT_COLONEL, 'Подполковник'),
        (COLONEL, 'Полковник'),
        (GENERAL, 'Генерал'),
    ]


class UserPosition:
    """
    Класс, который содержит должности.
    """

    OPERATOR = 'operator'
    SENIOR_OPERATOR = 'senior_operator'
    LEADER_LABORATORY = 'leader_laboratory'
    EMPLOYEE = 'employee'
    ENGINEER = 'engineer'

    STATUS_CHOICES = [
        (OPERATOR, 'Оператор'),
        (SENIOR_OPERATOR, 'Старший оператор'),
        (LEADER_LABORATORY, 'Начальник лаборатории'),
        (EMPLOYEE, 'Сотрудник лаборатории'),
        (ENGINEER, 'Инженер'),
    ]


class NumberAppeal:
    """
    Класс, который содердит номер призыва (1 ли 2)
    """

    ONE = 1
    TWO = 2

    CHOICES = [
        (ONE, '1'),
        (TWO, '2'),
    ]


class UserStatus:
    """
    Статус оператора
    """

    ARMY_SERVICE = 'army_service'
    CIVIL_SERVICE = 'civil_service'
    DEMOB = 'demob'

    STATUS_CHOICES = [
        (ARMY_SERVICE, 'Военная служба'),
        (CIVIL_SERVICE, 'Гражданская служба'),
        (DEMOB, 'Демобилизация'),
    ]
