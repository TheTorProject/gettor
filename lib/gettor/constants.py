#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
"""
 constants.py

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>,
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

"""

# Giant multi language help message. Add more translations as they become ready
multilangpackagehelpmsg = """
    Hello, This is the "GetTor" robot.

    I will mail you a Tor package, if you tell me which one you want.
    Please select one of the following package names:

        tor-browser-bundle
        macosx-i386-bundle
        macosx-ppc-bundle
        tor-im-browser-bundle
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
    tor-im-browser-bundle
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
    tor-im-browser-bundle
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
    tor-im-browser-bundle
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
    tor-im-browser-bundle
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
    tor-im-browser-bundle
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
        tor-im-browser-bundle
                         (Tor+Pidgin聚合聊天程序+Firefox浏览器)
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

# Short string to build mails follow
hello_gettor = _("""
    Hello, This is the "GetTor" robot.

    Thank you for your request.

    """)
help_dkim_1 = _("""
    Unfortunately, we won't answer you at this address. You should make
    an account with GMAIL.COM or YAHOO.CN and send the mail from
    one of those.

    """)
help_dkim_2 = _("""
    We only process requests from email services that support "DKIM",
    which is an email feature that lets us verify that the address in the
    "From" line is actually the one who sent the mail.

    """)
help_dkim_3 = _("""
    (We apologize if you didn't ask for this mail. Since your email is from
    a service that doesn't use DKIM, we're sending a short explanation,
    and then we'll ignore this email address for the next day or so.)

    """)
help_dkim_4 = _("""
    Please note that currently, we can't process HTML emails or base 64
    mails. You will need to send plain text.

    """)

help_dkim_5 = _("""
    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

    """)
choose_package_1 = _("""
    I will mail you a Tor package, if you tell me which one you want.
    Please select one of the following package names:

    """)
avail_packs = """
        tor-browser-bundle
        macosx-i386-bundle
        macosx-ppc-bundle
        tor-im-browser-bundle
        source-bundle
    
    """
choose_package_2 = _("""
    Please reply to this mail (to gettor@torproject.org), and tell me
    a single package name anywhere in the body of your email.

    """)
obtain_localized_head = _("""
    OBTAINING LOCALIZED VERSIONS OF TOR
    """)
obtain_localized_underline = """
    ===================================

    """
obtain_localized_1 = _("""
    To get a version of Tor translated into your language, specify the
    language you want in the address you send the mail to:

    """)
obtain_localized_2 = """
        gettor+zh@torproject.org

    """
obtain_localized_3 = _("""
    This example will give you the requested package in a localized
    version for Chinese. Check below for a list of supported language
    codes.

    """)
list_of_langs_head = _("""
    List of supported locales:
    """)
list_of_langs_underline = """
    -------------------------

    """
list_of_langs_1 = _("""
    Here is a list of all available languages:

    """)
list_of_langs_2 = _("""
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
    gettor+zh@torproject.org:     Chinese

    """)
list_of_langs_3 = _("""
    If you select no language, you will receive the English version.

    """)
support = _("""
    SUPPORT
    """)
support_underline = """
    =======
    """
support_email = _("""
    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

    """)
package_mail_1 = _("""
    Here's your requested software as a zip file. Please unzip the
    package and verify the signature.

    """)
package_mail_2 = _("""
    Hint: If your computer has GnuPG installed, use the gpg
    commandline tool as follows after unpacking the zip file:

    """)
package_mail_3 = _("""
       gpg --verify <packagename>.asc <packagename>

    """)
package_mail_4 = _("""
    The output should look somewhat like this:

    """)
package_mail_5 = """
       gpg: Good signature from "Roger Dingledine <arma@mit.edu>"

    """
package_mail_6 = _("""
    If you're not familiar with commandline tools, try looking for
    a graphical user interface for GnuPG on this website:

    """)
package_mail_7 = """
       http://www.gnupg.org/related_software/frontends.html

    """
package_mail_8 = _("""
    If your Internet connection blocks access to the Tor network, you
    may need a bridge relay. Bridge relays (or "bridges" for short)
    are Tor relays that aren't listed in the main directory. Since there
    is no complete public list of them, even if your ISP is filtering
    connections to all the known Tor relays, they probably won't be able
    to block all the bridges.

    """)
package_mail_9 = _("""
    You can acquire a bridge by sending an email that contains "get bridges"
    in the body of the email to the following email address:
    bridges@torproject.org

    """)
package_mail_10 = _("""
    It is also possible to fetch bridges with a web browser at the following
    url: https://bridges.torproject.org/

    """)
split_package_1 = _("""
    IMPORTANT NOTE:
    Since this is part of a split-file request, you need to wait for
    all split files to be received by you before you can save them all
    into the same directory and unpack them by double-clicking the
    first file.

    """)
split_package_2 = _("""
    Packages might come out of order! Please make sure you received
    all packages before you attempt to unpack them!

    """)
delay_alert_1 = _("""
    Thank you for your request. It was successfully understood. Your request is
    currently being processed. Your package should arrive within the next ten
    minutes.

    """)
delay_alert_2 = _("""
    If it doesn't arrive, the package might be too big for your mail provider.
    Try resending the mail from a gmail.com or yahoo.cn account. Also,
    try asking for tor-browser-bundle rather than tor-im-browser-bundle,
    since it's smaller.

    """)
error_mail = _("""
    Unfortunately we are currently experiencing problems and we can't fulfill
    your request right now. Please be patient as we try to resolve this issue.

    """)

# Build the actual mail texts
packagehelpmsg = hello_gettor + choose_package_1 + avail_packs + choose_package_2 + \
                 obtain_localized_head + obtain_localized_underline + \
                 obtain_localized_1 + obtain_localized_2 + obtain_localized_3 + \
                 list_of_langs_head + list_of_langs_underline + \
                 list_of_langs_1 + list_of_langs_2 + list_of_langs_3 + \
                 support + support_underline + support_email

helpmsg = hello_gettor + \
          help_dkim_1 + help_dkim_2 + help_dkim_3 + help_dkim_4 + help_dkim_5 + \
          support_email


packagemsg = hello_gettor + \
             package_mail_1 + package_mail_2 + package_mail_3 + package_mail_4 + \
             package_mail_5 + package_mail_6 + package_mail_7 + package_mail_8 + \
             package_mail_9 + package_mail_10 + \
             support_email


splitpackagemsg = hello_gettor + \
                  split_package_1 + split_package_2 + \
                  package_mail_1 + package_mail_2 + package_mail_3 + package_mail_4 + \
                  package_mail_5 + package_mail_6 + package_mail_7 + package_mail_8 + \
                  package_mail_9 + package_mail_10 + \
                  support_email


delayalertmsg = hello_gettor + \
                delay_alert_1 + delay_alert_2 + \
                support_email

mailfailmsg = hello_gettor + \
              support_email


