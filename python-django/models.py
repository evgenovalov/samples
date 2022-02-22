import random
import datetime

import math
import pytz
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.conf import settings
from django.utils import dateformat, timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.db.models import Avg, Max, Min, Model


from cleaning.validators import PhoneValidator, InvalidPhoneException

MIN_ORDER_PRICE = 350
COMMISSION_FACTOR = 1.00


class Category(models.Model):
    name = models.CharField(max_length=180, verbose_name="Название категории",
                            help_text="Введите название категории услуг")

    description = models.CharField(max_length=255, blank=True, default=None, verbose_name="Короткое описание",
                                   help_text="Короткое описание категории, которое рассказывает о находящихся "
                                             "в ней предметах. Выводится в списке категорий под названием категории.")

    icon = models.CharField(blank=True, max_length=100, verbose_name="SVG-иконка",
                            help_text="Векторное SVG-изображение, которое используется "
                                      "в качестве значка категории в меню")

    icon_url = models.FileField(upload_to="catalog/categories/", blank=False, verbose_name="SVG-иконка",
                                help_text="Загрузите SVG-изображение для данной услуги")

    enabled = models.BooleanField(default=False, verbose_name="Активация",
                                  help_text="Состояние категории. Включено: будет отображаться в меню")

    sort_number = models.PositiveSmallIntegerField(blank=True, default=0, verbose_name="Порядок сортировки",
                                                   help_text="Порядковый номер категории в блоках вывода категорий")

    date_created = models.DateTimeField(verbose_name="Дата создания", help_text="Дата создания объекта",
                                        auto_now_add=True, editable=False)

    date_changed = models.DateTimeField(verbose_name="Дата изменения", help_text="Дата последнего изменения объекта",
                                        auto_now=True, editable=False)

    class Meta:
        get_latest_by = 'date_created'
        ordering = ['name']
        verbose_name = "категория вещей"
        verbose_name_plural = "категории вещей"

    def __str__(self):
        return '%s' % self.name


class Subject(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name="Категория вещи")

    services = models.ManyToManyField('Service', through='SubjectService', verbose_name="Услуги для данной вещи",
                                      help_text="Услуги, применяемые к данной вещи")

    name = models.CharField(max_length=70, blank=False, verbose_name="Название предмета",
                            help_text="Название вещи выводится в области содержимого категории")

    image = models.ImageField(upload_to="catalog/subjects/", blank=True, max_length=200,
                              verbose_name="Изображение вещи",
                              help_text="Обложка, которая будет отображена в каталоге вещей")

    sort_number = models.PositiveSmallIntegerField(blank=True, default=0, verbose_name="Порядок сортировки",
                                                   help_text="Порядковый номер вещи в блоках вывода")

    description = models.CharField(blank=True, default=None, max_length=255, verbose_name="Описание вещи",
                                   help_text="Используется при выводе блока вещи")

    enabled = models.BooleanField(default=False, verbose_name="Доступно для заказа",
                                  help_text="Включите, если хотите, чтобы данная вещь была отображена на сайте")

    MEASUREMENT_TYPES = (
        ('KG', 'кг'),
        ('PCS', 'шт'),
        ('M2', 'м²'),
        ('SET', 'комплект'),
    )


    measurement_type = models.CharField(max_length=3, blank=False, choices=MEASUREMENT_TYPES,
                                        verbose_name="Единица измерения",
                                        help_text="В каких единицах измерения будет использоваться данная вещь")


    iteration_count = models.FloatField(default=1, verbose_name="Минимальная итерация",
                                        help_text="Минимальная итерация (порог увеличения) одной единицы вещи")


    table_weight_enabled = models.BooleanField(default=False, verbose_name="Таблица весов",
                                               help_text="Отображать ли таблицу весом под описанием данной вещи?")


    date_created = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Дата создания",
                                        help_text="Дата создания вещи")


    date_changed = models.DateTimeField(auto_now=True, editable=False, verbose_name="Последнее изменение",
                                        help_text="Дата последнего изменения вещи")

    class Meta:
        get_latest_by = 'date_created'
        ordering = ['name']
        verbose_name = "вещь"
        verbose_name_plural = "вещи"

    def image_url(self):
        if self.image:
            return self.image.url
        else:
            return ''


    def min_price(self):
        return SubjectService.objects.filter(subject=self.pk).aggregate(Min('price'))['price__min'] or 0

    def __str__(self):
        return '%s' % self.name


class Service(models.Model):

    name = models.CharField(max_length=100, blank=False, verbose_name="Отображаемое имя",
                            help_text="Введите короткое отображаемое имя для данной услуги")


    icon = models.CharField(max_length=100, blank=False, default="washing", verbose_name="Иконка услуги",
                            help_text="Название SVG-символа услуги, напр. 'washing'")


    icon_url = models.FileField(upload_to="catalog/services/", blank=False, verbose_name="SVG-иконка",
                                help_text="Загрузите SVG-изображение для данной услуги")


    units_count = models.PositiveIntegerField(editable=False, default=0, verbose_name="Количество единиц",
                                              help_text="Количество единиц данной услуги в заказах")


    date_created = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Дата создания",
                                        help_text="Дата создания услуги")


    date_changed = models.DateTimeField(auto_now=True, editable=False, verbose_name="Последнее изменение",
                                        help_text="Дата последнего изменения услуги")

    class Meta:
        get_latest_by = 'date_created'
        ordering = ['name']
        verbose_name = "услуга"
        verbose_name_plural = "услуги"

    def __str__(self):
        return self.name



class SubjectService(models.Model):

    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, verbose_name="Предмет")


    service = models.ForeignKey('Service', on_delete=models.CASCADE, verbose_name="Услуга для предмета")


    price = models.PositiveSmallIntegerField(blank=False, verbose_name="Стоимость услуги для предмета",
                                             help_text="Стоимость оказываемой услуги для указанного предмета")


    duration = models.PositiveIntegerField(default=5, verbose_name="Длительность обработки",
                                           help_text="Укажите среднюю длительность обработки указанной "
                                                     "услуги в минутуах (напр. длительность 1 футболки)")


    enabled = models.BooleanField(default=True, verbose_name="Активировать",
                                  help_text="Включите или выключите данную услугу для предмета. "
                                            "Отключенные услуги не отображаются в области предмета")


    orders_summary = models.PositiveIntegerField(default=0, editable=False, verbose_name="Общее количество заказов",
                                                 help_text="Общее количество заказов данной услуги для "
                                                           "текущего предмета за всё время")


    orders_now = models.PositiveIntegerField(default=0, editable=False, verbose_name="Количество активных заказов",
                                             help_text="Количество активных заказов данной услуги для этого предмета")


    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания",
                                        help_text="Дата создания услуги для текущего предмета")


    date_changed = models.DateTimeField(auto_now=True, verbose_name="Дата последнего изменения",
                                        help_text="Дата последнего изменения услуги")

    class Meta:
        get_latest_by = 'date_created'
        ordering = ['date_created']
        verbose_name = "услуга для вещи"
        verbose_name_plural = "услуги для вещи"

    def __str__(self):
        return '%s - %s' % (self.subject, self.service)


class CartUnit(models.Model):

    subject_service = models.ForeignKey('SubjectService', blank=False, on_delete=models.CASCADE,
                                        verbose_name="Элемент корзины")


    units_count = models.FloatField(blank=False, verbose_name="Количество единиц услуги",
                                    help_text="Общее количество единиц заказанной услуги")


    units_total = models.PositiveIntegerField(blank=True, default=0, verbose_name="Сумма по данной услуге",
                                              help_text="Сумма по данной услуге, применимой к вещи")


    date_created = models.DateTimeField(auto_now_add=True, editable=False)


    date_changed = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        get_latest_by = 'date_created'
        ordering = ['date_created']
        verbose_name = "элемент корзины"
        verbose_name_plural = "элементы корзины"

    def __str__(self):
        return '%s (%s ед.)' % (self.subject_service, self.units_count)


class Cart(models.Model):

    units = models.ManyToManyField('CartUnit', verbose_name="Элементы корзины")


    date_created = models.DateTimeField(auto_now_add=True, editable=False)


    date_changed = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        get_latest_by = 'date_changed'
        ordering = ['-date_changed']
        verbose_name = "корзина"
        verbose_name_plural = "корзины"

    def __str__(self):
        return 'Корзина #%s' % self.pk


class Order(models.Model):

    cart = models.ForeignKey('Cart', related_name="order_cart", on_delete=models.CASCADE, blank=False, default=None,
                             verbose_name="Корзина",
                             help_text="ID корзины, к которой прикреплен заказ")

    actual_cart = models.ForeignKey('Cart', null=True, blank=True, on_delete=models.SET_DEFAULT, default=None,
                                    verbose_name="Фактическая корзина",
                                    help_text="Корзина по факту поступления вещей на склад")


    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, on_delete=models.CASCADE,
                              verbose_name="ID пользователя-владельца заказа")


    delivery_lat = models.FloatField(blank=False, verbose_name="Широта доставки",
                                     help_text="Точная координата широты для доставки заказа заказчику")


    delivery_long = models.FloatField(blank=False, verbose_name="Долгота доставки",
                                      help_text="Точная координата долготы для доставки заказа заказчику")


    delivery_address = models.CharField(blank=False, max_length=255, verbose_name="Адрес доставки",
                                        help_text="Точный адрес доставки услуг, указанный при заказе")





    ORDER_STATUSES = (
        ('CANCELED', 'Отменён'),
        ('ISSUED', 'Оформлен'),
        ('WAITING', 'Ожидает курьера'),
        ('ACCEPTED', 'Принят курьером'),
        ('PROCESSING', 'Обслуживается'),
        ('TRANSIT', 'Доставляется'),
        ('DELIVERED', 'Доставлен'),
    )


    status = models.CharField(max_length=10, blank=False, default='ISSUED', choices=ORDER_STATUSES,
                              verbose_name="Статус заказа", help_text="Отображает текущий статус заказа")


    delivery_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата и время доставки",
                                         help_text="Рассчитанные дата и время доставки заказа")


    delivery_price = models.PositiveIntegerField(
        blank=False,
        default=0,
        editable=False,
        verbose_name="Стоимость доставки",
        help_text="Стоимость доставки заказа (наценка до мин. стоимости)"
    )


    payment_check = models.BooleanField(default=False, verbose_name="Проверка оплаты",
                                        help_text="Прошла ли проверку оплата заказа")


    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания",
                                        help_text="Дата создания заказа", editable=False)


    date_changed = models.DateTimeField(auto_now=True, editable=False, verbose_name="Дата обновления",
                                        help_text="Дата последнего изменения заказа")


    payment_method = models.ForeignKey('PaymentMethod', blank=True, default=None, on_delete=models.CASCADE,
                                       verbose_name="Способ оплаты",
                                       help_text="Способ оплаты заказа")


    yandex_payment_id = models.CharField(
        blank=True,
        default='',
        max_length=255,
        editable=False,
        verbose_name="Идентификатор платежа",
        help_text="Идентификатор платежа Яндекс.Кассы"
    )

    YANDEX_PAYMENT_STATUSES = (
        ('pending', 'Платёж не завершен'),
        ('waiting_for_capture', 'Ожидает подтверждения'),
        ('succeeded', 'Успешный платёж'),
        ('canceled', 'Платёж отменён'),
    )

    yandex_payment_status = models.CharField(blank=True, choices=YANDEX_PAYMENT_STATUSES, max_length=50,
                                             verbose_name="Статус платежа",
                                             help_text="Статус платежа платежной системы Яндекс.Касса")

    yandex_payment_confirmation_url = models.CharField(blank=True, max_length=255,
                                                       verbose_name="URL подтверждения",
                                                       help_text="URL для подтверждения платежа, проведённого клиентом",
                                                       editable=False)

    total = models.PositiveIntegerField(blank=False, editable=False, verbose_name="Сумма заказа",
                                        help_text="Сумма заказа, подлещая оплате на момент создания")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.delivery_price = self.calculate_delivery_price()
            self.total = math.floor(self.calculate_summary() + self.delivery_price)
        super(Order, self).save(*args, **kwargs)

    def calculate_delivery_price(self):
        summary = self.calculate_summary()
        return MIN_ORDER_PRICE - summary if summary < MIN_ORDER_PRICE else 0

    def calculate_summary(self):
        summary = 0
        for unit in self.cart.units.all():
            summary += unit.units_count * SubjectService.objects.get(pk=unit.subject_service.pk).price

        if self.payment_method.prepayed:
            summary *= COMMISSION_FACTOR

        return summary

    class Meta:
        get_latest_by = 'date_created'
        ordering = ['-date_created']
        verbose_name = "заказ"
        verbose_name_plural = "заказы"

    def __str__(self):
        return 'Заказ №%d' % self.pk


class MyUserManager(BaseUserManager):
    def create_user(self, phone, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """

        if not phone:
            raise ValueError('Пользователь должен ввести номер телефона')

        international_phone = PhoneValidator(phone).international

        user = self.model(
            phone=international_phone,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        international_phone = PhoneValidator(phone).international

        user = self.create_user(
            phone=international_phone,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class SMSVerifier(models.Model):
    phone = models.CharField(max_length=12, unique=True, verbose_name="Номер телефона",
                             help_text="Номер мобильного телефона, который необходим для идентификации аккаунта")

    code = models.CharField(max_length=6, verbose_name="Проверочный код",
                            help_text="Проверочный код идентификации телефонного номера")

    attempts_count = models.PositiveSmallIntegerField(default=0, verbose_name="Количество попыток",
                                                      help_text="Количество попыток с момента последней генерации")

    update_date = models.DateTimeField(auto_now=True, verbose_name="Время обновления",
                                       help_text="Дата и время последнего обновления проверочного кода")

    code_expiration_time = 300

    max_attempts_count = 5

    class Meta:
        get_latest_by = 'update_date'
        ordering = ['-update_date']
        verbose_name = "SMS-токен"
        verbose_name_plural = "SMS-токены"

    def __str__(self):
        return "%s #%d" % ("Верификация", self.pk)

    @staticmethod
    def set_new_code(phone):
        code = SMSVerifier.generate_4code()

        phone_validator = PhoneValidator(phone)

        try:
            verifier = SMSVerifier.objects.get(phone=phone_validator.international)
            if SMSVerifier.code_expired(verifier.update_date):
                verifier.code = code
                verifier.attempts_count = 0
                verifier.save()

                response = {
                    'status': True,
                    'message': 'Новый код установлен',
                    'code': code
                }

                return response
            else:
                response = {
                    'status': False,
                    'message': 'Вы не можете установить новый код до истечения %d секунд от предыдущего' %
                               SMSVerifier.code_expiration_time
                }

                return response
        except SMSVerifier.DoesNotExist:
            verifier = SMSVerifier.objects.create(phone=phone, code=code)

            response = {
                'status': True,
                'message': 'Новый код установлен',
                'code': code
            }

            return response

    @staticmethod
    def generate_4code():
        code = '%d' % random.randint(1000, 9999)
        return code

    @staticmethod
    def code_expired(update_date):
        delta = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) - update_date
        return True if delta.seconds > SMSVerifier.code_expiration_time else False

    @staticmethod
    def validate(phone, code):
        international = PhoneValidator(phone).international

        response = {
            'status': False,
            'message': 'Незвестная ошибка валидации SMS-кода'
        }

        try:

            verifier = SMSVerifier.objects.get(phone=international)
            if verifier.attempts_count >= SMSVerifier.max_attempts_count:
                response['status'] = False
                response['message'] = 'Вы превысили максимальное количество попыток ввода SMS-кода'
                return response
            else:
                if verifier.code == code:
                    verifier.attempts_count = 0
                    verifier.save()
                    response['status'] = True
                    response['message'] = 'Код принят'
                    return response
                else:
                    verifier.attempts_count += 1
                    verifier.save()
                    response['status'] = False
                    response['message'] = 'Вы ввели неправильный код'
                    return response
        except SMSVerifier.DoesNotExist:

            response['status'] = False
            response['message'] = 'На указанный Вами номер не отправлялся SMS-код'
            return response


class User(AbstractBaseUser):
    first_name = models.CharField(max_length=30, blank=True, verbose_name='Имя пользователя',
                                  help_text="Имя пользователя для обращения")

    phone = models.CharField(max_length=30, blank=False, unique=True, verbose_name="Телефон",
                             help_text="Номер мобильного телефона, который необходим для идентификации аккаунта")

    USERNAME_FIELD = 'phone'

    email = models.EmailField(verbose_name='Адрес email', help_text='Адрес электронной почты', blank=True)

    EMAIL_FIELD = 'email'

    phone_confirmation = models.BooleanField(default=False, verbose_name="Подтверждение телефона",
                                             help_text="Статус подтверждения телефона")

    last_visit = models.DateTimeField(default=timezone.now, verbose_name="Последний визит",
                                      help_text="Дата и время последнего визита пользователя в системе", blank=True)

    date_joined = models.DateTimeField(verbose_name='Дата регистрации', default=timezone.now)

    is_active = models.BooleanField(default=True, verbose_name="Включить аккаунт",
                                    help_text="Активировать аккаунт пользователя")

    is_admin = models.BooleanField(default=False, verbose_name="Это администратор",
                                   help_text="Права супер-пользователя")

    objects = MyUserManager()

    REQUIRED_FIELDS = []

    class Meta:
        get_latest_by = 'date_joined'
        ordering = ['-date_joined']
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def get_full_name(self):
        return self.phone

    def get_short_name(self):
        return self.phone

    def __str__(self):
        return self.phone

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"

        return True

    @property
    def is_staff(self):
        return self.is_admin


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Client(User):
    last_lat = models.FloatField(blank=True, default=0, verbose_name="Последняя широта",
                                 help_text="Широта, которая была зарегистрирована при последнем "
                                           "посещении сервиса пользователем")

    last_long = models.FloatField(blank=True, default=0, verbose_name="Последняя долгота",
                                  help_text="Долгота, которая была зарегистрирована при последнем "
                                            "посещении сервиса пользователем")

    home_lat = models.FloatField(blank=True, default=0, verbose_name="Домашняя широта",
                                 help_text="Широта, указанная пользователем как широта по-умолчанию")

    home_long = models.FloatField(blank=True, default=0, verbose_name="Домашняя долгота",
                                  help_text="Долгота, указанная пользователем как долгота по-умолчанию")

    home_address = models.CharField(blank=True, default='', max_length=255, verbose_name="Домашний адрес",
                                    help_text="Адрес доставки заказа, указанный пользователем")

    class Meta:
        get_latest_by = 'date_joined'
        ordering = ['-date_joined']
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"

    def __str__(self):
        return '%s (%s)' % (self.first_name, self.phone)

    def saved_payment_sources(self):
        return SavedBankCard.objects.filter(client=self.pk)


class SavedBankCard(models.Model):
    client = models.ForeignKey(to=Client, on_delete=models.CASCADE, verbose_name="Владелец карты",
                               help_text="Клиент-владелец данной банковской карты")

    last4 = models.CharField(max_length=4, verbose_name="Последние 4 цифры",
                             help_text="Последние 4 цифры номера банковской карты")

    yandex_payment_source_id = models.CharField(max_length=128, verbose_name="ID источника оплаты",
                                                help_text="Идентификатор сохраненной банковской карты Яндекс.Кассы")

    card_type = models.CharField(max_length=32, verbose_name="Тип карты",
                                 help_text="Тип банковской карты (Visa, MasterCard и др.)")

    class Meta:
        ordering = ['-client']
        verbose_name = "банковская карта"
        verbose_name_plural = "банковские карты"

    def __str__(self):
        return '%s (%s)' % (self.last4, self.card_type)


class Driver(User):
    active_orders = models.ManyToManyField('Order', through='DriverOrder', related_name="driver_orders",
                                           verbose_name="Активные заказы водителя",
                                           help_text="Текущие активные заказы водителя")

    last_reg_coords_date = models.DateTimeField(blank=True, null=True, default=None,
                                                verbose_name="Дата последней регистрации координат",
                                                help_text="Дата последней регистрации координат водителя")

    last_lat = models.FloatField(blank=True, null=True, default=None, verbose_name="Последняя широта",
                                 help_text="Широта, которая была зарегистрирована при последнем "
                                           "посещении сервиса водителем")

    last_long = models.FloatField(blank=True, null=True, default=None, verbose_name="Последняя долгота",
                                  help_text="Долгота, которая была зарегистрирована при последнем "
                                            "посещении сервиса водителем")

    class Meta:
        get_latest_by = 'date_joined'
        ordering = ['-date_joined']
        verbose_name = "водитель"
        verbose_name_plural = "водители"


class DriverOrder(models.Model):
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, verbose_name="Водитель заказа",
                               help_text="Водитель для текущего заказа")

    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name="Заказ",
                              help_text="Заказ, принятый водителем")

    date_arrival = models.DateTimeField(verbose_name="Время прибытия",
                                        help_text="Ориентировочное время прибытия в точку заказа в момент старта "
                                                  "(принятия заказа)")

    date_applied = models.DateTimeField(verbose_name="Дата принятия", help_text="Дата принятия заказа водителем",
                                        auto_now_add=True)

    class Meta:
        get_latest_by = 'date_applied'
        ordering = ['-date_applied']
        verbose_name = "маршрутный заказ"
        verbose_name_plural = "маршрутные заказы"


class PaymentMethod(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название", help_text="Название способа оплаты")

    description = models.CharField(max_length=255, verbose_name="Описание", help_text="Описание способа оплаты")

    icon = models.CharField(max_length=100, verbose_name="ID иконки", help_text="Идентификатор SVG-иконки из спрайта")

    icon_url = models.FileField(upload_to="catalog/payment-methods/", blank=False, verbose_name="SVG-иконка",
                                help_text="Загрузите SVG-изображение для данного способа оплаты")

    prepayed = models.BooleanField(verbose_name="Предоплата", help_text="Это способ оплаты с предоплатой?")

    payment_method_data_type = models.CharField(blank=True, default='', max_length=100, verbose_name="Способ оплаты",
                                                help_text="Служебный код способа оплаты на Яндекс.Кассе")

    CONFIRMATION_TYPES = (
        ('not', 'Без подтверждения'),
        ('redirect', 'Перенаправление'),
        ('external', 'Внешний способ'),
    )
    confirmation_type = models.CharField(max_length=20, choices=CONFIRMATION_TYPES, verbose_name="Способ подтверждения",
                                         help_text="Выберите способ верификации платежа Яндекс.Кассы")

    return_url = models.CharField(blank=True, default='', max_length=255, verbose_name="URL редиректа",
                                  help_text="URL, на который пользователи будут попадать после оплаты заказа")

    enabled = models.BooleanField(verbose_name="Активация",
                                  help_text="Включите или отключите данный способ оплаты заказа в системе")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"


class Administrator(User):
    class Meta:
        get_latest_by = 'date_joined'
        ordering = ['-date_joined']
        verbose_name = "администратор"
        verbose_name_plural = "администраторы"
