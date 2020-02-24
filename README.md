# Shell-PyMail

Shell-PyMail, henceforth called PyMail, is a quick and dirty way to send emails from a Linux command line without the need to install applications like postfix or deal with the old school sendmail. I find it ideal for use in containers where the idea is to keep them light, and access to a local mail daemon is unnecessary (beneficial for private hosted VM's and private hosted containers where the isp blocks some outgoing mail ports, specifically server to server access). PyMail does not run as a service and consequently consumes no RAM or CPU time at all when it is not in use.

PyMail is not intended to be a monitor for a system in any way but was designed with the idea that scripts which would be doing monitoring or other work could easily issue a single line command to send an email containing log information or reports about various activities.

## Requirements

- Linux OS (Tested on Ubuntu 18.04+)
- Python 3.6+
- Email Address and password on a mail server that allows STARTTLS connections (Google works).

## Install

PyMail has a built in install command that should function on most Linux systems. The install location will be in `/opt/shell_pymail` by way of simply copying the script to that location. Symbolic links will be created to `/usr/local/bin/pymail.sh` and `/usr/local/bin/pymail` as a matter of convenience.

This non-conventional install method is more a tool for myself and the way I use the script than anything. Installing this way allows the script to be used in environments where pip and/or git are not installed. The install should not be used if you are intending to import shell-pymail as a module.

`# /path/to/script/pymail.py install` 

## Setup

After following the Install instructions setup takes one more step.

**NOTE**: Install should **NOT** be run after this command. If you do run install after running this command then you should re-run the setup, or manually move the props.json file to the same `/opt/shell_pymail` directory after running install

`# pymail setup server port login from-address email_to_for_test_mail`

- **server**: ip or address to mail server. Ex: mail.google.com OR 216.58.214.197
- **port**: port that the application should connect to on the mail server. (Ex: 587)
- **login**: login name to authenticate - usually an email address. Ex: user@gmail.com
- **from-address**: The email address that should be used in the "from" field in the email.
- **email_to_for_test_mail**: The email address to send a test email to when the setup is complete.

## Use

You can get help to remind you of the following commands by running:

`# pymail send-mail --help`

To send a basic email, assuming successful setup simply execute

`# pymail send-mail to_address@domain.com "The email subject" "The body message"`

If you'd like to send a pre-formatted text as the body you can do the following:

`# pymail send-mail to_address@domain.com "The email subject" "/full/path/to/plane/text/file.txt`

If you'd like to attach a file to your email, such as a log file to be sent, you can use:

`# pymail send-mail to_address@domain.com "The email subject" "/full/path/to/plane/text/file.txt --file=/path/to/log/file/attach.log`

## FAQ

##### Why do I have to run the script as root?

The program is used to send email anywhere, and as often as it is called. If not requiring the script be run by a specific privileged user, there would be no other protection in place to keep a normal user or a compromised machine from sending email spam using this utility. `sudo` or executing the command as root when a script is run as root was the easiest/most secure solution for my use case.

You can change the user that has privileges to send email with this script by setting the `PERMITTED_USER_ID` on line 46 appropriately. Be warned, as stated above, using a non-privileged user would greatly increase the inherent risk of having such a script on your computer.

## Copyright/License

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
