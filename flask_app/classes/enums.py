from enum import Enum


class NOTIFICATION_TYPE(Enum):
    FOLLOWED_USER = 1
    FOLLOW_REQUEST = 2
    FOLLOW_CREATED_RECIPE = 3


NOTIFICATION_TYPE_SET = NOTIFICATION_TYPE._value2member_map_


class USER_SEXES_TYPE(Enum):
    MALE = "M"
    FEMALE = "F"
    NOT_ASSIGN = "NA"


USER_TYPE_SET = USER_SEXES_TYPE._value2member_map_


class RECIPES_BACKGROUND_TYPE(Enum):
    LIKED = "L"
    SAVED = "S"


RECIPES_BACKGROUND_TYPE_SET = RECIPES_BACKGROUND_TYPE._value2member_map_


class FOLLOWED_STATE_SET(Enum):
    FOLLOWED = "F"
    NOT_FOLLOWED = "NF"
    PENDING_FOLLOWED = "PF"


USER_TYPE_SET = FOLLOWED_STATE_SET._value2member_map_


class UNITS_TYPE(Enum):
    GRAMS = "g"
    UNITS = "U"
    DENTES = "D"
    FOLHA = "F"
    MILILITROS = "ml"
    QB = "QB"


UNITS_TYPE_SET = UNITS_TYPE._value2member_map_


class USER_TYPE(Enum):
    NORMAL = "N"
    COMPANY = "C"
    VIP = "V"
    ADMIN = "A"


USER_TYPE_SET = USER_TYPE._value2member_map_


class CALENDER_ENTRY_TAG(Enum):
    PEQUENO_ALMOCO = "PEQUENO ALMOÇO"
    LANCHE_DA_MANHA = "LANCHE DA MANHÃ"
    ALMOCO = "ALMOÇO"
    LANCHE_DA_TARDE = "LANCHE DA TARDE"  # (normal, company, vip, admin)
    JANTAR = "JANTAR"  # (normal, company, vip, admin)
    CEIA = "CEIA"  # (normal, company, vip, admin)


CALENDER_ENTRY_TAG_SET = CALENDER_ENTRY_TAG._value2member_map_


class PROFILE_TYPE(Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


PROFILE_TYPE_SET = PROFILE_TYPE._value2member_map_
