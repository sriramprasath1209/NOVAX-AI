import io
import os
import tempfile
import unittest
import json
from src.db import Database
from src import auth
import src.db
import src.brain
import src.memory
import src.conversation
from src.web_app import NOVAXRequestHandler, wsgi_app, HTML_PAGE


class TestWSGIApp(unittest.TestCase):

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

        self.test_db = Database(self.db_path)
        auth.db = self.test_db
        src.db.db = self.test_db
        src.brain.db = self.test_db
        src.memory.db = self.test_db
        src.conversation.db = self.test_db

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_wsgi_get_root(self):
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/",
            "QUERY_STRING": "",
            "wsgi.input": io.BytesIO(b""),
            "CONTENT_LENGTH": "0"
        }
        status_captured = []
        headers_captured = []

        def start_response(status, headers):
            status_captured.append(status)
            headers_captured.append(headers)

        body = wsgi_app(environ, start_response)
        self.assertTrue(len(status_captured) > 0)
        self.assertTrue(status_captured[0].startswith("200"))
        response_text = b"".join(body).decode("utf-8")
        self.assertIn("NOVAX-AI", response_text)

    def test_wsgi_get_auth_me(self):
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/api/auth/me",
            "QUERY_STRING": "",
            "wsgi.input": io.BytesIO(b""),
            "CONTENT_LENGTH": "0"
        }
        status_captured = []
        headers_captured = []

        def start_response(status, headers):
            status_captured.append(status)
            headers_captured.append(headers)

        body = wsgi_app(environ, start_response)
        self.assertTrue(len(status_captured) > 0)
        self.assertTrue(status_captured[0].startswith("200"))
        res_json = json.loads(b"".join(body).decode("utf-8"))
    def test_wsgi_signup_and_login(self):
        signup_payload = json.dumps({
            "email": "test@novax.ai",
            "password": "Password123!",
            "name": "Test User"
        }).encode("utf-8")

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/auth/signup",
            "QUERY_STRING": "",
            "wsgi.input": io.BytesIO(signup_payload),
            "CONTENT_LENGTH": str(len(signup_payload)),
            "CONTENT_TYPE": "application/json",
            "HTTP_X_FORWARDED_FOR": "1.2.3.4"
        }
        status_captured = []
        headers_captured = []

        def start_response(status, headers):
            status_captured.append(status)
            headers_captured.append(headers)

        body = wsgi_app(environ, start_response)
        self.assertTrue(status_captured[0].startswith("200"), f"Status was {status_captured}")
        res_json = json.loads(b"".join(body).decode("utf-8"))
        self.assertTrue(res_json.get("success"))
        self.assertEqual(res_json["user"]["email"], "test@novax.ai")

    def test_wsgi_reset_password(self):
        # 1. Signup
        signup_payload = json.dumps({"email": "reset@novax.ai", "password": "OldPassword1!", "name": "Reset User"}).encode("utf-8")
        environ_signup = {
            "REQUEST_METHOD": "POST", "PATH_INFO": "/api/auth/signup", "QUERY_STRING": "",
            "wsgi.input": io.BytesIO(signup_payload), "CONTENT_LENGTH": str(len(signup_payload)), "CONTENT_TYPE": "application/json"
        }
        wsgi_app(environ_signup, lambda s, h: None)

        # 2. Reset Password
        reset_payload = json.dumps({"email": "reset@novax.ai", "password": "NewPassword2!"}).encode("utf-8")
        environ_reset = {
            "REQUEST_METHOD": "POST", "PATH_INFO": "/api/auth/reset-password", "QUERY_STRING": "",
            "wsgi.input": io.BytesIO(reset_payload), "CONTENT_LENGTH": str(len(reset_payload)), "CONTENT_TYPE": "application/json"
        }
        status_captured = []
        body = wsgi_app(environ_reset, lambda s, h: status_captured.append(s))
        self.assertTrue(status_captured[0].startswith("200"))
        res_json = json.loads(b"".join(body).decode("utf-8"))
        self.assertTrue(res_json.get("success"))

        # 3. Login with new password
        login_payload = json.dumps({"email": "reset@novax.ai", "password": "NewPassword2!"}).encode("utf-8")
        environ_login = {
            "REQUEST_METHOD": "POST", "PATH_INFO": "/api/auth/login", "QUERY_STRING": "",
            "wsgi.input": io.BytesIO(login_payload), "CONTENT_LENGTH": str(len(login_payload)), "CONTENT_TYPE": "application/json"
        }
        status_login = []
        body_login = wsgi_app(environ_login, lambda s, h: status_login.append(s))
        self.assertTrue(status_login[0].startswith("200"))


if __name__ == "__main__":
    unittest.main()


