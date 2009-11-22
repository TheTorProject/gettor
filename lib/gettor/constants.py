#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
"""
 constants.py

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

"""

import gettext

_ = gettext.gettext

helpmsg = _("""
    Hello! This is the "GetTor" robot.

    Unfortunately, we won't answer you at this address. You should make
    an account with GMAIL.COM or YAHOO.CN and send the mail from
    one of those.

    We only process requests from email services that support "DKIM",
    which is an email feature that lets us verify that the address in the
    "From" line is actually the one who sent the mail.

    (We apologize if you didn't ask for this mail. Since your email is from
    a service that doesn't use DKIM, we're sending a short explanation,
    and then we'll ignore this email address for the next day or so.)

    Please note that currently, we can't process HTML emails or base 64
    mails. You will need to send plain text.

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org
        """)

packagehelpmsg = _("""
    Hello, This is the "GetTor" robot.

    I will mail you a Tor package, if you tell me which one you want.
    Please select one of the following package names:

        tor-browser-bundle
        macosx-universal-bundle
        panther-bundle
        tor-im-browser-bundle
        source-bundle

    Please reply to this mail (to gettor@torproject.org), and tell me
    a single package name anywhere in the body of your email.

    Please note that GetTor can send out localized versions of Tor.
    In your mail to us, please add a line containing "Lang:" followed by
    the language abbreviation like so:

    Lang: language

    For example if you want the tor-browser-bundle for in chinese, write
    us an email with the following text:

    ---
    tor-browser-bundle
    Lang: zh-CN
    ---

    Or, if you want the tor-browser-bundle in farsi, write us an email
    with the following text:

    ---
    tor-browser-bundle
    Lang: fa-IR
    ---

    Here is a list of all available languages:

    ar:     Arabic
    de:     German
    en-US:  English
    es-ES:  Spanish
    fa-IR:  Farsi (Iran)
    fr:     French
    it:     Italian
    nl:     Dutch
    pl:     Polish
    ru:     Russian
    zh-CN:  Chinese

    If you select no language, you will receive the english version.

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

        """)

packagemsg = _("""
    Hello! This is the "GetTor" robot.

    Here's your requested software as a zip file. Please unzip the
    package and verify the signature.

    Hint: If your computer has GnuPG installed, use the gpg
    commandline tool as follows after unpacking the zip file:

       gpg --verify <packagename>.asc <packagename>

    The output should look somewhat like this:

       gpg: Good signature from "Roger Dingledine <arma@mit.edu>"

    If you're not familiar with commandline tools, try looking for
    a graphical user interface for GnuPG on this website:

       http://www.gnupg.org/related_software/frontends.html

    If your Internet connection blocks access to the Tor network, you
    may need a bridge relay. Bridge relays (or "bridges" for short)
    are Tor relays that aren't listed in the main directory. Since there
    is no complete public list of them, even if your ISP is filtering
    connections to all the known Tor relays, they probably won't be able
    to block all the bridges.

    You can acquire a bridge by sending an email that contains "get bridges"
    in the body of the email to the following email address:
    bridges@torproject.org

    It is also possible to fetch bridges with a web browser at the following
    url: https://bridges.torproject.org/

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

        """)

splitpackagemsg = _("""
    Hello! This is the "GetTor" robot.

    Here's your requested software as a zip file. Please unzip the
    package and verify the signature.

    IMPORTANT NOTE:
    Since this is part of a split-file request, you need to wait for 
    all split files to be received by you before you can save them all
    into the same directory and unpack them by double-clicking the 
    first file. 

    Packages might come out of order! Please make sure you received
    all packages before you attempt to unpack them!

    Hint: If your computer has GnuPG installed, use the gpg
    commandline tool as follows after unpacking the zip file:

       gpg --verify <packagename>.asc <packagename>

    The output should look somewhat like this:

       gpg: Good signature from "Roger Dingledine <arma@mit.edu>"

    If you're not familiar with commandline tools, try looking for
    a graphical user interface for GnuPG on this website:

       http://www.gnupg.org/related_software/frontends.html

    If your Internet connection blocks access to the Tor network, you
    may need a bridge relay. Bridge relays (or "bridges" for short)
    are Tor relays that aren't listed in the main directory. Since there
    is no complete public list of them, even if your ISP is filtering
    connections to all the known Tor relays, they probably won't be able
    to block all the bridges.

    You can acquire a bridge by sending an email that contains "get bridges"
    in the body of the email to the following email address:
    bridges@torproject.org

    It is also possible to fetch bridges with a web browser at the following
    url: https://bridges.torproject.org/

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

        """)

delayalertmsg = _("""
    Hello, This is the "GetTor" robot.

    Thank you for your request. It was successfully understood. Your request is
    currently being processed. Your package should arrive within the next ten
    minutes.

    If it doesn't arrive, the package might be too big for your mail provider.
    Try resending the mail from a gmail.com or yahoo.cn account. Also,
    try asking for tor-browser-bundle rather than tor-im-browser-bundle,
    since it's smaller.

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

            """)

mailfailmsg = _("""
    Hello, This is the "GetTor" robot.

    Thank you for your request.

    Unfortunatly we are currently experiencing problems and we can't fulfill
    your request right now. Please be patient as we try to resolve this issue.

        """)
    
