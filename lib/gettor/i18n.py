# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.
# -*- coding: utf-8 -*-

import os
import gettext

def getLang(lang, config):
    """Return the Translation instance for a given language. If no Translation
       instance is found, return the one for 'en'
    """
    localeDir = os.path.join(config.BASEDIR, "i18n")
    fallback = config.DEFAULT_LOCALE
    return gettext.translation("gettor", localedir=localeDir,
                               languages=[lang], fallback=fallback)

def _(text):
    """This is necessary because strings are translated when they're imported.
       Otherwise this would make it impossible to switch languages more than 
       once
    """
    return text

# Giant multi language help message. Add more translations as they become ready
MULTILANGHELP = """
    Hello, This is the "GetTor" robot.

    I will mail you a Tor package, if you tell me which one you want.
    Please select one of the following package names:

        tor-browser-bundle
        macosx-i386-bundle
        macosx-ppc-bundle
        linux-browser-bundle-i386
        linux-browser-bundle-x86_64
        source-bundle

    Please reply to this mail (to gettor), and tell me
    a single package name anywhere in the body of your email.

    OBTAINING LOCALIZED VERSIONS OF TOR
    ===================================

    To get a version of Tor translated into your language, specify the
    language you want in the address you send the mail to:

        gettor+zh

    This example will give you the requested package in a localized
    version for Chinese. Check below for a list of supported language
    codes.

    List of supported locales:
    -------------------------

    Here is a list of all available languages:

    gettor+ar:     Arabic
    gettor+de:     German
    gettor+en:     English
    gettor+es:     Spanish
    gettor+fa:     Farsi (Iran)
    gettor+fr:     French
    gettor+it:     Italian
    gettor+nl:     Dutch
    gettor+pl:     Polish
    gettor+ru:     Russian
    gettor+zh:     Chinese

    If you select no language, you will receive the English version.

    SUPPORT
    =======

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants

    --

    مرحبا، أنا روبوت \"احصل على تور\".
    
    سأرسل لك حزمة برامج تور، إذا أخبرتني أيها تريد.
    رجاء اختر إحدى أسماء الحزم التالية:
    
    tor-browser-bundle
    macosx-i386-bundle
    macosx-ppc-bundle
    linux-browser-bundle-i386
    linux-browser-bundle-x86_64
    source-bundle
    
    يرجى أن ترد على هذه الرسالة (إلى gettor@torproject.org)، وتخبرني
    باسم حزمة واحدة فقط في أي مكان ضمن رسالة الرد.
    
    الحصول على إصدارات مترجمة من تور
    ========================
    
    لتحصل على إصدار تور مترجم إلى لغتك، يرجى أن تحدد
    اللغة التي تريد ضمن العنوان الذي سترسل الرسالة الإلكترونية إليه:
    
    gettor+zh@torproject.org
    
    هذا المثال يعطيك الحزمة المطلوبة مترجمة
    للغة الصينية. تحقق من القائمة أدناه لتجد رموز اللغات
    المدعومة.
    
    قائمة اللغات المدعومة:
    -------------------
    
    ها هي قائمة اللغات المتوفرة:
    
    gettor+ar@torproject.org: العربية
    gettor+de@torproject.org: الألمانية
    gettor+en@torproject.org: الإنكليزية
    gettor+es@torproject.org: الإسبانية
    gettor+fa@torproject.org: الفارسية
    gettor+fr@torproject.org: الفرنسية
    gettor+it@torproject.org: الإيطالية
    gettor+nl@torproject.org: الهولندية
    gettor+pl@torproject.org: البولندية
    gettor+ru@torproject.org: الروسية
    gettor+zh@torproject.org: الصينية
    
    إن لم تقم باختيار لغة فستحصل على الإصدارة الإنكليزية.
    
    الدعم الفني
    =======
    
    إن كانت لديك أية أسئلة أو إذا لم يعمل هذا الحل يمكنك الاتصال بكائن
    بشري على عنوان الدعم الفني التالي: tor-assistants@torproject.org

    --

    سلام! روبات "GetTor" در خدمت شماست. 
    
    چنانچه به من بگویید که به کدامیک از بسته های Tor  نیاز دارید، آن را برای شما 
    ارسال خواهم کرد. 
    لطفا یکی از بسته های را زیر با ذکر نام انتخاب کنید:  
    
    tor-browser-bundle
    macosx-i386-bundle
    macosx-ppc-bundle
    linux-browser-bundle-i386
    linux-browser-bundle-x86_64
    source-bundle

    لطفا به این نامه پاسخ داده ( به آدرس gettor@torproject.org ) و در قسمتی از 
    متن ایمیل خود نام یکی از بسته های فوق را ذکر کنید. 
    
    تهیه نسخه ترجمه شده  TOR  
    ===================================
    
    برای دریافت نسخه ای از TOR  ترجمه شده به زبان محلی شما، می بایستی زبان مورد 
    نظر خود را در آدرس گیرنده ایمیل ذکر کنید. بعنوان مثال:  
    
    gettor+zh@torproject.org

    در این مثال، فرستنده خواهان نسخه ترجمه شده به زبان چینی می باشد. برای آگاهی 
    از کدهای مربوط به زبانهای قابل پشتیبانی توسط Tor ، فهرست زیر را مطالعه کنید: 
    فهرست زبانهای پشتیانی شده
    -------------------------

    gettor+ar@torproject.org: Arabic
    gettor+de@torproject.org: German
    gettor+en@torproject.org: English
    gettor+es@torproject.org: Spanish
    gettor+fa@torproject.org: Farsi (Iran)
    gettor+fr@torproject.org: French
    gettor+it@torproject.org: Italian
    gettor+nl@torproject.org: Dutch
    gettor+pl@torproject.org: Polish
    gettor+ru@torproject.org: Russian
    gettor+zh@torproject.org: Chinese

    چنانچه هیچیک از زبانهای فوق را انتخاب نکنید، نسخه انگلیسی برای شما ارسال 
    خواهد شد. 
    
    پشتیبانی 
    =======
    
    چنانچه سوالی دارید یا برنامه دچار اشکال بوده و کار نمی کند ، با قسمت 
    پشتیبانی با آدرس زیر تماس بگیرید تا یک انسان به سوال شما پاسخ دهد: tor-assistants@torproject.org

    --

    Hei, dette er "GetTor"-roboten
    
    Jeg kommer til å sende deg en Tor-pakke, hvis du forteller meg hvilken du 
    vil ha.
    Vennligst velg en av følgende pakkenavn:
    
    tor-browser-bundle
    macosx-i386-bundle
    macosx-ppc-bundle
    linux-browser-bundle-i386
    linux-browser-bundle-x86_64
    source-bundle

    Vennligst svar til denne eposten (til gettor@torproject.org), og nevn
    kun et enkelt pakkenavn i tekstområdet til eposten din.
    
    SKAFFE LOKALISERTE VERSJONER AV TOR
    ===================================

    For å skaffe en versjon av Tor som har blitt oversatt til ditt språk,
    spesifiser språket du vil i epostadressen du sender eposten til:

    gettor+zh@torproject.org

    Dette eksempelet vil gi deg en forespurt pakke som er en oversatt
    versjon for kinesisk. Se listen nedenfor for hvilke språk det er støtte for.

    Liste av støttede språk:
    -------------------------

    Her er en liste av språkene som er tilgjengelig:

    gettor+ar@torproject.org: Arabisk
    gettor+de@torproject.org: Tysk
    gettor+en@torproject.org: Engelsk
    gettor+es@torproject.org: Spansk
    gettor+fa@torproject.org: Farsi (Iran)
    gettor+fr@torproject.org: Fransk
    gettor+it@torproject.org: Italiensk
    gettor+nl@torproject.org: Nederlandsk
    gettor+pl@torproject.org: Polsk
    gettor+ru@torproject.org: Russisk
    gettor+zh@torproject.org: Kinesisk

    Hvis du ikke spesifiserer noen språk vil du motta standard Engelsk
    versjon

    STØTTE
    =======

    Hvis du har noen spørsmål eller det ikke virker, kan du kontakte et
    menneske på denne support-eposten: tor-assistants@torproject.org

    --

    Olá! Este é o robot "GetTor".

    Eu envio-lhe um pacote Tor, bastando para isso dizer qual o que quer. 
    Escolha um dos seguintes pacotes:

    tor-browser-bundle
    macosx-i386-bundle
    macosx-ppc-bundle
    linux-browser-bundle-i386
    linux-browser-bundle-x86_64
    source-bundle

    Por favor responda a esta email (para gettor@torproject.org), e diga qual o 
    pacote que deseja, colocando o seu nome no corpo do seu email.

    OBTER VERSÕES TRADUZIDAS DO TOR
    ===================================

    Para lhe ser enviado uma versão traduzida do Tor, especifique a língua no 
    destinatário do seu email:

    gettor+zh@torproject.org

    Este exemplo vai enviar o pacote traduzido para Chinês Simplificado. Veja a 
    lista de endereços de email existentes que pode utilizar:

    Lista de endereços de email suportados:
    -------------------------

    gettor+pt@torproject.org: Português
    gettor+ar@torproject.org: Arábico
    gettor+de@torproject.org: Alemão
    gettor+en@torproject.org: Inglês
    gettor+es@torproject.org: Espanhol
    gettor+fa@torproject.org: Farsi (Irão)
    gettor+fr@torproject.org: Francês
    gettor+it@torproject.org: Italiano
    gettor+nl@torproject.org: Holandês
    gettor+pl@torproject.org: Polaco
    gettor+ru@torproject.org: Russo
    gettor+zh@torproject.org: Chinês

    Se não escolher nenhuma língua, receberá o Tor em Inglês.

    SUPORTE
    =======

    Se tiver alguma dúvida, pode contactar um humano através do seguinte 
    endereço: tor-assistants@torproject.org

    --

    Здравствуйте! Это "робот GetTor".

    Я отошлю вам пакет Tor если вы укажете который вы хотите.
    Пожалуйста выберите один из пакетов:

    tor-browser-bundle
    macosx-i386-bundle
    macosx-ppc-bundle
    linux-browser-bundle-i386
    linux-browser-bundle-x86_64
    source-bundle

    Пожалуйста свяжитесь с нами по этой элктронной почте 
    (gettor@torproject.org), и укажите
    название одного из пакетов в любом месте в "теле" вашего письма.

    ПОЛУЧЕНИЕ ЛОКАЛИЗИРОВАННЫХ ВЕРСИЙ TOR
    ===================================

    Чтобы получить версию Tor переведенную на ваш язык,укажите
    предпочитаемый язык в адресной строке куда вы отослали электронную почту:

    gettor+zh@torproject.org

    Вышеуказанный пример даст вам запрошенный пакет в локализированной
    версии китайского языка. Проверьте ниже список кодов поддерживаемых
     языков.

    Список поддерживаемых регионов
    -------------------------

    Ниже указан список всех доступных языков:

    gettor+ar@torproject.org:   арабский
    gettor+de@torproject.org: немецкий
    gettor+en@torproject.org: английский
    gettor+es@torproject.org: испанский
    gettor+fa@torproject.org: фарси (Иран)
    gettor+fr@torproject.org: французский
    gettor+it@torproject.org: итальянский
    gettor+nl@torproject.org: голландский
    gettor+pl@torproject.org: польский
    gettor+ru@torproject.org: русский
    gettor+zh@torproject.org: китайский

    Если вы не выберите язык, вы получите версию на английском языке.

    ПОДДЕРЖКА
    =======

    Если у вас вопросы или что то не сработало, вы можете связаться 
    с живым представителем по этому электронному адресу:tor-assistants@torproject.org

    --

    你好, 这里是"GetTor"自动回复。

    您从这里可以得到Tor套件, 请告诉我您需要的套件种类.
    请选择套件名称:

        tor-browser-bundle
                         (Tor+Firefox浏览器)
        macosx-i386-bundle
                         (Tor for MacOS)
        macosx-ppc-bundle
                         (Tor for MacOS on PowerPC )
        linux-browser-bundle-i386
        linux-browser-bundle-x86_64
                         (Tor for Linux)
        source-bundle
                         (源码包)

    请直接回复本邮件(gettor@torproject.org), 
    并在信的正文中写好您所需要的套件名称（不包括括号内的中文）。

    获取其他语言的Tor套件
    ===================================

    在收件人地址中指定语言代码可以获得本对应语言的版本，例如：

        gettor+zh@torproject.org

    本例中，您将得到中文版的Tor套件，下面是目前支持的语种代码：

    支持语言列表:
    -------------------------

    全部可用语言列表:

    gettor+ar@torproject.org:     Arabic
    gettor+de@torproject.org:     German
    gettor+en@torproject.org:     English
    gettor+es@torproject.org:     Spanish
    gettor+fa@torproject.org:     Farsi (Iran)
    gettor+fr@torproject.org:     French
    gettor+it@torproject.org:     Italian
    gettor+nl@torproject.org:     Dutch
    gettor+pl@torproject.org:     Polish
    gettor+ru@torproject.org:     Russian
    gettor+zh@torproject.org:     中文

    如果您未指定语言代码，您将收到英文版。

    支持
    =======

    如果您遇到困难或服务出现问题，请联系我们的
    技术支持邮箱: tor-assistants@torproject.org

    --
        """


PACKAGEHELP = _("""
    Hello, This is the "GetTor" robot.

    I will mail you a Tor package, if you tell me which one you want.
    Please select one of the following package names:

        tor-browser-bundle
        macosx-i386-bundle
        macosx-ppc-bundle
        linux-browser-bundle-i386
        linux-browser-bundle-x86_64
        source-bundle


    Please reply to this mail (to gettor), and tell me a single package name anywhere in 
    the body of your email. To make your decision a bit easier, here's a short explanation 
    of what these packages are:

    tor-browser-bundle:

    The Tor Browser Bundle package for Windows operating systems. If you're running some 
    version of Windows, like Windows XP, Windows Vista or Windows 7, this is the package
    you should get.

    macosx-i386-bundle:

    The Tor Browser Bundle package for OS X, Intel CPU architecture. In general, newer 
    Mac hardware will require you to use this package.

    macosx-ppc-bundle:

    The Tor Browser Bundle package for OS X, PowerPC CPU architecture. In general, older
    Mac hardware will require you to use this package.

    linux-browser-bundle-i386:

    The Tor Browser Bundle package for Linux, 32bit versions. Note that this package is
    rather large and needs your email provider to allow for attachments of about 30MB in
    size.

    linux-browser-bundle-x86_64:

    The Tor Browser Bundle package for Linux, 64bit versions. Note that this package is
    rather large and needs your email provider to allow for attachements of about 30MB
    in size.

    source-bundle:

    The Tor source code. Only request this package if you know what you're doing. This
    isn't the package to use for a normal user.
""")

GETTOR_TEXT = [
 # GETTOR_TEXT[0]
_("""Hello, This is the "GetTor" robot.

Thank you for your request."""),
 # GETTOR_TEXT[1]
_(""" Unfortunately, we won't answer you at this address. You should make
an account with GMAIL.COM or YAHOO.CN and send the mail from
one of those."""),
 # GETTOR_TEXT[2]
_("""We only process requests from email services that support "DKIM",
which is an email feature that lets us verify that the address in the
"From" line is actually the one who sent the mail."""),
 # GETTOR_TEXT[3]
_("""(We apologize if you didn't ask for this mail. Since your email is from
a service that doesn't use DKIM, we're sending a short explanation,
and then we'll ignore this email address for the next day or so.)"""),
 # GETTOR_TEXT[4]
_("""Please note that currently, we can't process HTML emails or base 64
mails. You will need to send plain text."""),
 # GETTOR_TEXT[5]
_("""If you have any questions or it doesn't work, you can contact a
human at this support email address: tor-assistants@torproject.org"""),
 # GETTOR_TEXT[6]
_("""I will mail you a Tor package, if you tell me which one you want.
Please select one of the following package names:"""),
 # GETTOR_TEXT[7]
_("""Please reply to this mail (to gettor@torproject.org), and tell me
a single package name anywhere in the body of your email."""),
 # GETTOR_TEXT[8]
_(""" OBTAINING LOCALIZED VERSIONS OF TOR"""),
 # GETTOR_TEXT[9]
_("""To get a version of Tor translated into your language, specify the
language you want in the address you send the mail to:"""),
 # GETTOR_TEXT[10]
_("""This example will give you the requested package in a localized
version for Chinese. Check below for a list of supported language
codes. """),
 # GETTOR_TEXT[11]
_(""" List of supported locales:"""),
 # GETTOR_TEXT[12]
_("""Here is a list of all available languages:"""),
 # GETTOR_TEXT[13]
_("""    gettor+ar@torproject.org:     Arabic
    gettor+de@torproject.org:     German
    gettor+en@torproject.org:     English
    gettor+es@torproject.org:     Spanish
    gettor+fa@torproject.org:     Farsi (Iran)
    gettor+fr@torproject.org:     French
    gettor+it@torproject.org:     Italian
    gettor+nl@torproject.org:     Dutch
    gettor+pl@torproject.org:     Polish
    gettor+ru@torproject.org:     Russian
    gettor+zh@torproject.org:     Chinese"""),
 # GETTOR_TEXT[14]
_("""If you select no language, you will receive the English version."""),
 # GETTOR_TEXT[15]
_("""SMALLER SIZED PACKAGES"""),
 # GETTOR_TEXT[16]
_("""If your bandwith is low or your provider doesn't allow you to 
receive large attachments in your email, there is a feature of 
GetTor you can use to make it send you a number of small packages
instead of one big one."""),
 # GETTOR_TEXT[17]
_("""Simply include the keyword 'split' somewhere in your email like so:"""),
 # GETTOR_TEXT[18]
_("""Sending this text in an email to GetTor will cause it to send you 
the Tor Browser Bundle in a number of 1,4MB attachments."""),
 # GETTOR_TEXT[19]
_("""After having received all parts, you need to re-assemble them to 
one package again. This is done as follows:"""),
 # GETTOR_TEXT[20]
_("""1.) Save all received attachments into one folder on your disk."""),
 # GETTOR_TEXT[21]
_("""2.) Unzip all files ending in ".z". If you saved all attachments to
a fresh folder before, simply unzip all files in that folder."""),
 # GETTOR_TEXT[22]
_("""3.) Verify all files as described in the mail you received with 
each package. (gpg --verify)"""),
 # GETTOR_TEXT[23]
_("""4.) Now use a program that can unrar multivolume RAR archives. On
Windows, this usually is WinRAR. If you don't have that
installed on you computer yet, get it here:"""),
 # GETTOR_TEXT[24]
_("""To unpack your Tor package, simply doubleclick the ".exe" file."""),
 # GETTOR_TEXT[25]
_("""5.) After unpacking is finished, you should find a newly created 
".exe" file in your destination folder. Simply doubleclick
that and Tor Browser Bundle should start within a few seconds."""),
 # GETTOR_TEXT[26]
_("""6.) That's it. You're done. Thanks for using Tor and have fun!"""),
 # GETTOR_TEXT[27]
_("""SUPPORT"""),
 # GETTOR_TEXT[28]
_("""If you have any questions or it doesn't work, you can contact a
human at this support email address: tor-assistants@torproject.org"""),
 # GETTOR_TEXT[29]
_(""" Here's your requested software as a zip file. Please unzip the
package and verify the signature."""),
 # GETTOR_TEXT[30]
_("""Hint: If your computer has GnuPG installed, use the gpg
commandline tool as follows after unpacking the zip file:"""),
 # GETTOR_TEXT[31]
_("""The output should look somewhat like this:"""),
 # GETTOR_TEXT[32]
_("""If you're not familiar with commandline tools, try looking for
a graphical user interface for GnuPG on this website:"""),
 # GETTOR_TEXT[33]
_("""If your Internet connection blocks access to the Tor network, you
may need a bridge relay. Bridge relays (or "bridges" for short)
are Tor relays that aren't listed in the main directory. Since there
is no complete public list of them, even if your ISP is filtering
connections to all the known Tor relays, they probably won't be able
to block all the bridges."""),
 # GETTOR_TEXT[34]
_("""You can acquire a bridge by sending an email that contains "get bridges"
in the body of the email to the following email address:"""),
 # GETTOR_TEXT[35]
_("""It is also possible to fetch bridges with a web browser at the following
url: https://bridges.torproject.org/"""),
 # GETTOR_TEXT[36]
_("""IMPORTANT NOTE:
Since this is part of a split-file request, you need to wait for
all split files to be received by you before you can save them all
into the same directory and unpack them by double-clicking the
first file."""),
 # GETTOR_TEXT[37]
_("""Packages might arrive out of order! Please make sure you received
all packages before you attempt to unpack them!"""),
 # GETTOR_TEXT[38]
_("""It was successfully understood. Your request is currently being processed.
Your package should arrive within the next ten minutes."""),
 # GETTOR_TEXT[39]
_("""If it doesn't arrive, the package might be too big for your mail provider.
Try resending the mail from a GMAIL.COM or YAHOO.COM account."""),
 # GETTOR_TEXT[40]
_("""Unfortunately we are currently experiencing problems and we can't fulfill
your request right now. Please be patient as we try to resolve this issue."""),
 # GETTOR_TEXT[41]
_("""Unfortunately there is no split package available for the package you
requested. Please send us another package name or request the same package 
again, but remove the 'split' keyword. In that case we'll send you the whole 
package. Make sure this is what you want.""")
]
