gettor
======

GetTor Revamp (on development).
Google Summer of Code 2014.

* To get the current repo:
$ git clone https://github.com/ileiva/gettor.git

* To upload bundles to Dropbox and create a links file:

1) Install the Dropbox and GnuPG Python modules (just the first time):

$ pip install dropbox gnupg

2) Change account info in src/dropbox.py (app_key, app_secret, access_token)

3) Specify the path of the PGP key that signed the packages (to include fingerprint).

4) Run the script:

$ cd src/providers/;rm *.links;cd ..; python dropbox.py

If everything works good, you should see a dropbox.links file inside the 'providers' directory. The script will take the files on upload_dir (default to 'upload/') which end up on .xz and .xz.asc respectively. To add more locales for testing do the following (example for german):

$ cd upload; cp tor-browser-linux32-3.6.2_en-EN.tar.xz tor-browser-linux32-3.6.2_de-DE.tar.xz

$ cd upload; cp tor-browser-linux32-3.6.2_en-EN.tar.xz.asc tor-browser-linux32-3.6.2_de-DE.tar.xz.asc

A script for getting the latest bundles is pending.

* To test if the core module is working:

1) Use the dummy script provided:

$ python core_demo.py

* To test the smtp module (without mail server):

1) Set request parameters on smtp/sample/sample-email.eml (by default, 'To: gettor+en@torproject.org' and 'linux' in the body of the message. 

2) Run dummy script:

$ python smtp_demo.py < smtp/sample/sample-email.eml

If mail server is configured, then uncomment lines 328-332, 337, 353-359, and comment lines 334-335, 338, 360 on gettor/smtp.py. Also, you should enable e-mail forwarding as specified on https://gitweb.torproject.org/gettor.git/blob/HEAD:/README

* To test the xmpp module

1) Install the SleekXMPP module:

$ pip install sleekxmpp

2) Change user details on xmpp.cfg

3) Run dummy script.

$ python xmpp_demo.py

4) To communicate with the bot using Pidgin click on Friends -> New instant message. There are still some issues with bot responses.

The xmpp module has been used in the following providers:

 * dukgo.com (works)
 * riseup.net (works)
 * jabber.ccc.de (works)
 * jit.si (worked for a while, not any longer)

 




