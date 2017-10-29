import logging
import sys
import json
import os
import traceback
import zipfile
import tempfile

class Util:
    @staticmethod
    def success_response(data={}):
        response_body = {}

        status = {}
        status["reqStatus"] = "SUCCESS"

        response_body["status"] = status
        response_body["data"] = data
        print("Success Response: %s", json.dumps(response_body, indent=4))
        print("=======================================================")
        return response_body

    @staticmethod
    def error_response(code=500,
                       message="Internal Server Error",
                       tokens=[]):
        response_body = {}
        messages = []
        msg = {}
        msg["msgCode"] = code
        msg["msgText"] = message
        msg["msgValues"] = tokens

        messages.append(msg)

        status = {}
        status["reqStatus"] = "ERROR"
        status["messages"] = messages

        response_body["status"] = status
        print("Error Response: %s", json.dumps(response_body, indent=4))
        print("=======================================================")
        return response_body

    @staticmethod
    def read_file(file_name):
        with open(file_name) as data_file:
            data = data_file.read()
            return data

    @staticmethod
    def handle_exception(e):
        traceback.print_exc()
        res_body = {}
        if isinstance(e, ToscaOrchestratorException):
            print("received ToscaOrchestratorException")
            res_body = Util.error_response(e.code, e.message, e.tokens)
        elif isinstance(e, Exception):
            print("Exception occured")
            res_body = Util.error_response(500, str(e), {})
        else:
            print("Unknown Internal Exception %s", sys.exc_info()[0])
            res_body = Util.error_response()

        return res_body

    @staticmethod
    def zip_dir(dir_path, zip_file_path):
        """Zip the directory to the give file"""

        # Always remove the file if there is duplicate for now
        if os.path.isfile(zip_file_path):
            os.remove(zip_file_path)
        zipf = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                zipf.write(os.path.join(root, file),
                os.path.relpath(os.path.join(root, file),
                dir_path))
        zipf.close()

