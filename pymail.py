#!/usr/bin/env python3
"""
Copyright © 2019  David VanderWyst

Shell-PyMail is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Shell-PyMail is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.



Exit codes:
    NOTE: Exit codes are only valid when running the script from the command line, and do not apply
            if script is imported.

    1 - Real user id was not 0, root privileges are required to run this
            application. The application assumes that root uid is 0. If your
            root user's id is different than 0 you can set PERMITTED_USER_ID appropriately by
            changing it below.


"""

import argparse
import json
import logging
from os import getuid, path, mkdir, remove, symlink, chmod
from shutil import copy
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from getpass import getpass

VERSION = "0.0.1"
PERMITTED_USER_ID = 0
LOG_LEVEL = "DEBUG"

# Comment out second logging line in order to log to file., uncomment first in order to display logging messages
# to screen, rather than saving them to a file.
#
# NOTE: Only one logging.basicConfig line should be uncommented.
# logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)
logging.basicConfig(filename="shell-pymail.log", format='%(asctime)s:%(levelname)s:%(message)s', level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class Props(object):
    """Application properties."""

    def __init__(self):
        self.__email_server_address = ""
        self.__server_port = 0
        self.__email_login_name = ""
        self.__login_password = ""
        self.__default_from_email = ""

    @property
    def mail_server(self) -> str:
        return self.__email_server_address

    @mail_server.setter
    def mail_server(self, server_address: str):
        if not isinstance(server_address, str):
            raise TypeError("Expected string, got: {}".format(type(server_address)))

        self.__email_server_address = server_address

    @property
    def server_port(self) -> int:
        return self.__server_port

    @server_port.setter
    def server_port(self, port: int):
        if not isinstance(port, int):
            raise TypeError("Expected integer, got: {}".format(type(port)))

        self.__server_port = port

    @property
    def login_name(self) -> str:
        return self.__email_login_name

    @login_name.setter
    def login_name(self, val: str):
        if not isinstance(val, str):
            raise TypeError("Expected str, got: {}".format(type(val)))
        self.__email_login_name = val

    @property
    def login_password(self) -> str:
        return self.__login_password

    @login_password.setter
    def login_password(self, val: str):
        if not isinstance(val, str):
            raise TypeError("Expected str, got: {}".format(type(val)))
        self.__login_password = val

    @property
    def default_from_email(self) -> str:
        return self.__default_from_email

    @default_from_email.setter
    def default_from_email(self, val: str):
        if not isinstance(val, str):
            raise TypeError("Expected str, got: {}".format(type(val)))
        self.__default_from_email = val


class EMail(object):
    """
    Holds the information to be used to create and send an email.
    """

    def __init__(self):
        self.__email_to_address = ""
        self.__email_from_address = ""
        self.__email_subject = ""
        self.__body = ""
        self.__attachment_path = ""

    @property
    def to_email_addresses(self) -> str:
        return self.__email_to_address

    @to_email_addresses.setter
    def to_email_addresses(self, val: str):
        if not isinstance(val, str):
            raise TypeError("Expected str, got: {}".format(type(val)))
        self.__email_to_address = val

    @property
    def from_email_address(self) -> str:
        return self.__email_from_address

    @from_email_address.setter
    def from_email_address(self, val: str):
        if not isinstance(val, str):
            raise TypeError("Expected str, got: {}".format(type(val)))
        self.__email_from_address = val

    @property
    def subject(self) -> str:
        return self.__email_subject

    @subject.setter
    def subject(self, val: str):
        if not isinstance(val, str):
            raise TypeError("Expected str, got: {}".format(type(val)))
        self.__email_subject = val

    @property
    def email_body(self) -> str:
        return self.__body

    @email_body.setter
    def email_body(self, val: str):
        if not isinstance(val, str):
            raise TypeError("Expected str, got: {}".format(type(val)))

        if path.isfile(val):
            try:
                with open(val, "r") as f:
                    self.__body = f.read()
            except IOError as e:
                logger.exception("{}".format(e))
        else:
            self.__body = val

    @property
    def attachment_path(self) -> str:
        return self.__attachment_path

    @attachment_path.setter
    def attachment_path(self, val: str):
        if not isinstance(val, str):
            raise TypeError("Expected str, got: {}".format(type(val)))
        self.__attachment_path = val


class PyMailDAO(object):
    """
    Handles the saving and loading of application data.
    """
    @staticmethod
    def save_properties(props: Props) -> bool:

        json_string = json.dumps(props.__dict__, indent=4)

        prop_file = path.join(path.dirname(path.realpath(__file__)), "props.json")

        try:
            with open(prop_file, "w") as f:
                f.write(json_string)

            chmod(prop_file, 0o700)
            return True
        except IOError as e:
            logger.exception(e)
            return False

    @staticmethod
    def get_properties() -> Props:
        prop_file = path.join(path.dirname(path.realpath(__file__)), "props.json")

        p = Props()
        if not path.isfile(prop_file):
            logger.critical("Setup is not completed props.json file not found.")
            raise FileNotFoundError("The property file does not exist. Likely "
                                    "that setup was not completed correctly.\n"
                                    "run \"./pymail.py setup --help")
        try:
            with open(prop_file, "r") as f:
                props = json.loads(f.read())

            p.__dict__.update(props)

            return p

        except IOError as e:
            logger.exception(e)


class PyMail(object):
    """
    The PyMail class is the interface for Shell-PyMail. When importing Shell-PyMail into one of your
    own projects this would be the class to access in order to send mail.
    """
    @staticmethod
    def send_mail(em: EMail, properties: Props = None) -> bool:
        """
        Send Mail

        Uses the email and Props object passed in to send an email. If no Props is passed (It is set to None) then
        the method will attempt to load the Props from the props.json file.

        :param em: Email to be sent.
        :param properties: Union[Props, None]
        :return:
        """
        if not isinstance(em, EMail):
            raise TypeError("Expected Email, got {}".format(type(em)))

        if properties is not None and not isinstance(properties, Props):
            raise TypeError("Expected Props or None, got: {}".format(type(properties)))

        context = ssl.create_default_context()
        if properties is None:
            p = PyMailDAO.get_properties()
        else:
            p = properties

        msg = MIMEMultipart()

        if em.from_email_address.strip() == "":
            msg['From'] = p.default_from_email
        else:
            msg['From'] = em.from_email_address

        msg['To'] = em.to_email_addresses
        msg['Subject'] = em.subject

        msg.attach(MIMEText(em.email_body, 'plain'))

        if path.isfile(em.attachment_path):
            attachment = open(em.attachment_path, "rb")

            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            "attachment; filename= {}".format(path.basename(em.attachment_path.replace(" ", "_"))))

            msg.attach(part)

        try:
            server = smtplib.SMTP(p.mail_server, p.server_port)
            server.starttls(context=context)
            server.login(p.login_name, p.login_password)
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)
            server.quit()
            logger.info("Email set to: {}, with subject: {}")
            return True
        except smtplib.SMTPException as e:
            logger.exception("{}".format(e))
            return False

    @staticmethod
    def setup_app(properties: Props, em: EMail = None) -> bool:
        """
        Setups the application with initial values.

        Method will process and save all information to for connecting to an email server.

        :param properties : Props
                    Prepopulated Props object containing all information required for connecting to the server. The
                    password should be left blank when generating this object from the command line. When
                    the password is left blank it will be requested from the user.
        :param em : Union[EMail, None]
                    The email object, is used to send a test email using the newly entered setup information.
                    If the email property is set to None, no test email is sent.

        """
        if not isinstance(properties, Props):
            raise TypeError("Expected Props object, got: {}".format(type(properties)))
        if em is not None and not isinstance(em, EMail):
            raise TypeError("Expected EMail, or None for email, got: {}".format(type(em)))

        if properties.login_password.strip() == "":
            password1 = "one"
            password2 = "two"
            while password1 != password2:
                password1 = getpass("Password: ")
                password2 = getpass("Confirm Password: ")

            properties.login_password = password1

        if not PyMail.send_mail(em, properties):
            return False
        else:
            if PyMailDAO.save_properties(properties):
                return True
            else:
                logger.critical("Failed to save properties file during setup.")
                return False

    @staticmethod
    def install() -> bool:
        """
        Sets up the current system to use the application.

        Installs the application by copying the pymail.py file to the /opt/shell-pymail directory, and
        adding two symbolic links "pymail" and "pymail.py" to the /usr/local/bin/ folder.

        Note: This method will not execute when the module is imported.
        :return: bool
        """
        if not __name__ == "__main__":
            logger.error("The install method can not be called when PyMail used as module")
            return False

        current_path = path.realpath(__file__)

        if path.exists("/opt/shell_pymail/pymail.py") and current_path == "/opt/shell_pymail/pymail.py":
            logger.error("Install ran, but running from currently installed file. Must be run from new script file.")
            return False

        if not path.exists("/opt"):
            logger.error("/opt does not exist, and is required for automated setup at this time.")
            return False

        if not path.exists("/opt/shell_pymail"):
            mkdir(path="/opt/shell_pymail", mode=0o700)

        if path.exists("/opt/shell_pymail/pymail.py"):
            remove("/opt/shell_pymail/pymail.py")

        copy(current_path, "/opt/shell_pymail/pymail.py")

        if path.exists("/usr/local/bin"):
            symlink("/opt/shell_pymail/pymail.py", "/usr/local/bin/pymail")
            symlink("/opt/shell_pymail/pymail.py", "/usr/local/bin/pymail.py")

        return True


if __name__ == "__main__":
    # Restricting the script to running as root because giving access to a script that can endlessly send emails
    # could cause huge problems. Restricting the script to root seemed like a logical solution. The UID can be
    # changed in the top of the file by changing the PERMITTED_USER_ID value. If the user wants to create a specific
    # user to handle this script as well as logs, that is easily doable.
    if getuid() is not PERMITTED_USER_ID:
        print("Shell-PyMail requires root privileges.")
        exit(1)

    # ------------------------------------------------------------------------------------------------------------
    #
    #   Command line setup
    #
    # ------------------------------------------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Send email from shell.")

    # must set the dest variable in order to have the subparsers command show up in the Namespace object
    # in order to test_body.txt for it.
    subparsers = parser.add_subparsers(help="options", dest="command")

    # send email
    send_mail_parser = subparsers.add_parser("send-mail", help="Send mail")
    send_mail_parser.add_argument("mail_to", help="email address to send the email to.")
    send_mail_parser.add_argument("subject", help="subject of the email")
    send_mail_parser.add_argument("body", help="Body of the email. This can be the contents, "
                                               "or a file path to a file containing plain text.")
    send_mail_parser.add_argument("-f", "--file", help="Full file path to file to attach to email.\n"
                                                       "Example: --file=\"/my/path/file1.txt\"", default="")

    # run initial setup or rerun setup.
    app_setup = subparsers.add_parser("setup", help="Initial setup, or change initial setup options")
    app_setup.add_argument("server", help="The server that you connect to in order to send your email. Can be "
                                          "uri or ip address.\n"
                                          "Example: smtp.gmail.com")
    app_setup.add_argument("port", type=int, help="port number for outgoing mail."
                                                  "example: 587")
    app_setup.add_argument("login", help="Login for email server.\n"
                                         "example: username@gmail.com")
    app_setup.add_argument("from_address", help="EMail address your mail will be sent from.")
    app_setup.add_argument("test_to_email", help="Valid email to send a test email to.")

    app_install = subparsers.add_parser("install", help="Does basic application setup. Moves script to"
                                                        "/opt/shell_pymail/ and creates symlink to pymail")

    # ------------------------------------------------------------------------------------------------------------
    #
    #   Code to process command line entries by the user
    #
    # ------------------------------------------------------------------------------------------------------------
    parsed_obj = parser.parse_args()

    if parsed_obj.command == "install":
        if not PyMail.install():
            print("Install failed, check log for details.")
        else:
            print("Application setup successfully.\n"
                  "Run: 'sudo pymail setup --help' for details on setting up the application for initial use.")

    elif parsed_obj.command == "setup":
        app_p = Props()
        app_p.mail_server = parsed_obj.server
        app_p.server_port = parsed_obj.port
        app_p.login_name = parsed_obj.login
        app_p.default_from_email = parsed_obj.from_address
        email = EMail()
        email.to_email_addresses = parsed_obj.test_to_email
        email.from_email_address = parsed_obj.from_address
        email.subject = "Test email sent by Shell-PyMail"
        email.email_body = "Script setup has been completed successfully.\n\n" \
                           "If you've received this email, the script is setup and working correctly."
        if PyMail.setup_app(app_p, email):
            print("Setup was successful.")
        else:
            print("Setup failed, check the connection and login information for the email server.")

    elif parsed_obj.command == "send-mail":
        email = EMail()
        email.to_email_addresses = parsed_obj.mail_to
        email.subject = parsed_obj.subject
        email.email_body = parsed_obj.body
        email.attachment_path = parsed_obj.file

        PyMail.send_mail(email)
