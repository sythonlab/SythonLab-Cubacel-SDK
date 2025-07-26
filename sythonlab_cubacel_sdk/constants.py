from enum import Enum


class ActionsEnum(Enum):
    SALE_SIM_TUR = 'sale_sim_tur'
    GET_SERVICES = 'get_services'
    GET_PROVINCES = 'get_provinces'
    GET_NATIONALITIES = 'get_nationalities'
    GET_OFFICES = 'get_offices'
    GET_SALE = 'get_sale'
    RECHARGE = 'recharge'
    GET_BALANCE = 'get_balance'
    CHANGE_PASSWORD = 'change_password'
    REQUEST_BATCH = 'request_batch'
    GET_BATCH_SALE = 'get_batch_sale'
    CANCEL_BATCH_SALE = 'cancel_batch_sale'
    SALE_SIM_TUR_CARD = 'sale_sim_tur_card'
    GET_IDENTIFICATION_TYPES = 'get_identification_types'
    CANCEL_SALE = 'cancel_sale'
