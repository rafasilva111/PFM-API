import unittest

import psycopg2
import json

import requests
from constants import *
from functions import delete_user, _make_request, _print_response, get_user


class PersistDataTest(unittest.TestCase):
    endpoint = f"{BASE_URL}/auth"

    def test_read_from_pg(self):

        self.assertEqual(1, 5)

    def test_create_user_request(self):

        """
            Constants
        """

        expected_status_code = 201
        endpoint = "/auth"

        """

            Default behavior

        """

        """ 
            Class model incomplete
        """

        print("Creating incomplete account")

        class_model = {
            "name": TEST_ACCOUNT_1_DEFAULT_NAME,
            "username": TEST_ACCOUNT_1_DEFAULT_USERNAME,
            "birth_date": TEST_ACCOUNT_1_DEFAULT_BIRTHDATE,
            "email": TEST_ACCOUNT_1,
            "password": TEST_ACCOUNT_1_PASSWORD,
            "img_source": TEST_ACCOUNT_1_DEFAULT_IMAGE_SOURCE,
            "sex": TEST_ACCOUNT_1_DEFAULT_SEX,
        }

        expected_data = None

        " execution "

        response = get_user(TEST_ACCOUNT_1_DEFAULT_USERNAME)

        if response:
            delete_user(response['id'])

        response = _make_request('POST', endpoint=endpoint, data=class_model, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        """ 
            Class model complete
        """

        class_model_complete = {
            "name": TEST_ACCOUNT_2_DEFAULT_NAME,
            "username": TEST_ACCOUNT_2_DEFAULT_USERNAME,
            "birth_date": TEST_ACCOUNT_2_DEFAULT_BIRTHDATE,
            "email": TEST_ACCOUNT_2,
            "password": TEST_ACCOUNT_2_PASSWORD,
            "img_source": TEST_ACCOUNT_2_DEFAULT_IMAGE_SOURCE,
            "sex": TEST_ACCOUNT_2_DEFAULT_SEX,
            "weight": TEST_ACCOUNT_2_DEFAULT_WEIGHT,
            "activity_level": TEST_ACCOUNT_2_DEFAULT_ACTIVITY_LEVEL,
            "height": TEST_ACCOUNT_2_DEFAULT_HEIGHT
        }

        " execution "

        response = get_user(TEST_ACCOUNT_2_DEFAULT_USERNAME)

        if response:
            delete_user(response['id'])

        response = _make_request('POST', endpoint=endpoint, data=class_model_complete, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        """
            
            Validations
            
        """

        class_model_complete = {
            "name": TEST_ACCOUNT_3_DEFAULT_NAME,
            "username": TEST_ACCOUNT_3_DEFAULT_USERNAME,
            "birth_date": TEST_ACCOUNT_2_DEFAULT_BIRTHDATE,
            "email": TEST_ACCOUNT_3,
            "password": TEST_ACCOUNT_3_PASSWORD,
            "img_source": TEST_ACCOUNT_2_DEFAULT_IMAGE_SOURCE,
            "sex": TEST_ACCOUNT_2_DEFAULT_SEX,
            "weight": TEST_ACCOUNT_2_DEFAULT_WEIGHT,
            "activity_level": TEST_ACCOUNT_2_DEFAULT_ACTIVITY_LEVEL,
            "height": TEST_ACCOUNT_2_DEFAULT_HEIGHT
        }

        " username "

        print()
        print("[=] Username Testing [=]")
        print("[=]")

        # test uniqueness

        ## expected
        expected_status_code = 400
        expected_data = {'errors': {'username': ['Username is already being used.']}}

        class_model_complete['username'] = TEST_ACCOUNT_2_DEFAULT_USERNAME

        ## execution

        response = _make_request('POST', endpoint=endpoint, data=class_model_complete, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        class_model_complete['username'] = TEST_ACCOUNT_3_DEFAULT_USERNAME

        self.assertDictEqual(response.json(), expected_data, "Response data does not match expectations")

        " birthdate "

        print()
        print("[=] BirthDate Testing [=]")
        print("[=]")

        # + 12 anos

        ## expected
        expected_status_code = 400
        expected_data = {'errors': {'birth_date': ['You must be at least 12 years old']}}

        class_model_complete['birth_date'] = TEST_ACCOUNT_ERROR_BIRTHDATE

        ## execution

        response = _make_request('POST', endpoint=endpoint, data=class_model_complete, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        class_model_complete['birth_date'] = TEST_ACCOUNT_2_DEFAULT_BIRTHDATE

        self.assertDictEqual(response.json(), expected_data, "Response data does not match expectations")

        " weight "

        print()
        print("[=] Weight Testing [=]")
        print("[=]")
        # < 30

        ## expected
        expected_status_code = 400
        expected_data = {'errors': {'weight': ['You must be between 30 kg and 200 kg']}}

        class_model_complete['weight'] = TEST_ACCOUNT_ERROR_WEIGHT_UNDER

        ## execution

        response = _make_request('POST', endpoint=endpoint, data=class_model_complete, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        class_model_complete['weight'] = TEST_ACCOUNT_2_DEFAULT_WEIGHT

        self.assertDictEqual(response.json(), expected_data, "Response data does not match expectations")

        # > 200

        ## expected
        expected_status_code = 400
        expected_data = {'errors': {'weight': ['You must be between 30 kg and 200 kg']}}

        class_model_complete['weight'] = TEST_ACCOUNT_ERROR_WEIGHT_OVER

        ## execution

        response = _make_request('POST', endpoint=endpoint, data=class_model_complete, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        class_model_complete['weight'] = TEST_ACCOUNT_2_DEFAULT_WEIGHT

        self.assertDictEqual(response.json(), expected_data, "Response data does not match expectations")

        " height "

        print()
        print("[=] Height Testing [=]")
        print("[=]")

        # < 100

        ## expected
        expected_status_code = 400
        expected_data = {'errors': {'height': ['You must be between 100 cm and 300 cm']}}

        class_model_complete['height'] = TEST_ACCOUNT_ERROR_HEIGHT_UNDER

        ## execution

        response = _make_request('POST', endpoint=endpoint, data=class_model_complete, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        class_model_complete['weight'] = TEST_ACCOUNT_2_DEFAULT_WEIGHT

        self.assertDictEqual(response.json(), expected_data, "Response data does not match expectations")

        # > 200

        ## expected
        expected_status_code = 400
        expected_data = {'errors': {'height': ['You must be between 100 cm and 300 cm']}}

        class_model_complete['height'] = TEST_ACCOUNT_ERROR_HEIGHT_OVER

        ## execution

        response = _make_request('POST', endpoint=endpoint, data=class_model_complete, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        class_model_complete['height'] = TEST_ACCOUNT_2_DEFAULT_WEIGHT

        self.assertDictEqual(response.json(), expected_data, "Response data does not match expectations")

        # format

        ## expected
        expected_status_code = 400
        expected_data = {'errors': {'height': ['You must be between 100 cm and 300 cm']}}

        class_model_complete['height'] = TEST_ACCOUNT_ERROR_HEIGHT_FORMAT

        ## execution

        response = _make_request('POST', endpoint=endpoint, data=class_model_complete, headers=HEADERS)

        _print_response(response)

        self.assertEqual(response.status_code, expected_status_code, "Unexpected status code")

        class_model_complete['height'] = TEST_ACCOUNT_2_DEFAULT_WEIGHT

        self.assertDictEqual(response.json(), expected_data, "Response data does not match expectations")


        " activity level "


if __name__ == '__main__':
    unittest.main()
