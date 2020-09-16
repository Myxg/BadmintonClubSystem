#coding: utf-8

from jsonschema import validate


regist_user_schema = {
    "title": "",
    "type": "object",
    "properties": {
        "username": {
            "type": "string"
        },
        "email": {
            "type": "string"
        },
        "password1": {
            "type": "string"
        },
        "password2": {
            "type": "string"
        },
        "user_type": {
            "type": "integer"
        }
    },
    "required": ["username", "password1", "password2", "user_type"]
}
