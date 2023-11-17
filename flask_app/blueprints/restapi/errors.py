from re import sub
from typing import Tuple, Dict


def return_error_sql(e: str) -> tuple[dict[str, str], int]:
    error_str = sub(r"[()]", "", str(e.__cause__)).split(",")
    error_code = error_str[0]
    error_message = error_str[1].replace(r"\\", "").replace('"', "")
    return {"message": error_message, "code": error_code}, 500


def student_no_exists(id: str) -> tuple[dict[str, str], int]:
    return {"message": f"The student with ID {id} does not exist"}, 404


def school_no_exists(id: str) -> tuple[dict[str, str], int]:
    return {"message": f"The schol with ID {id} does not exist"}, 404
