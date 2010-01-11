#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
"""
 constants.py

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>,
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

"""

# Giant multi language help message. Add more translations as they become ready
multilanghelpmsg = """
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

    --

    Ù~EØ±Ø­Ø¨Ø§! Ø£Ù~FØ§ Ø±Ù~HØ¨Ù~HØª "Ø§Ø­ØµÙ~D Ø¹Ù~DÙ~I ØªÙ~HØ±".

    Ù~DÙ~DØ£Ø³Ù~A Ù~DÙ~F Ù~FØ±Ø¯ Ø¹Ù~DÙ~JÙ~C Ø¹Ù~DÙ~I Ù~GØ°Ø§ Ø§Ù~DØ¹Ù~FÙ~HØ§Ù~F. Ù~JØªÙ~HØ¬Ø¨ Ø¹Ù~DÙ~JÙ~C Ø£Ù~F ØªÙ~FØ´Ø¦
    Ø­Ø³Ø§Ø¨Ø§Ù~K Ø¹Ù~DÙ~I GMAIL.COM Ø£Ù~H YAHOO.COM Ù~HØªØ±Ø³Ù~D Ø±Ø³Ø§Ù~DØ© Ø¥Ù~DÙ~CØªØ±Ù~HÙ~FÙ~JØ©
    Ù~EÙ~F 
    Ø£Ø­Ø¯Ù~GÙ~EØ§.

    Ù~FÙ~BÙ~HÙ~E Ø¨Ù~EØ¹Ø§Ù~DØ¬Ø© Ø§Ù~DØ·Ù~DØ¨Ø§Øª Ù~EÙ~F Ø®Ø¯Ù~EØ§Øª Ø§Ù~DØ¨Ø±Ù~JØ¯ Ø§Ù~DØªÙ~J ØªØ¯Ø¹Ù~E "DKIM"Ø~L
    Ù~HÙ~GÙ~J Ø®Ø§ØµØ© ØªØ³Ù~EØ­ Ù~DÙ~FØ§ Ø¨Ø§Ù~DØªØ­Ù~BÙ~B Ù~EÙ~F Ø£Ù~F Ø§Ù~DØ¹Ù~FÙ~HØ§Ù~F Ù~AÙ~J
    Ø­Ù~BÙ~D Ø§Ù~DÙ~EØ±Ø³Ù~D Ù~GÙ~H Ø¨Ø§Ù~DÙ~AØ¹Ù~D Ù~EÙ~F Ù~BØ§Ù~E Ø¨Ø¥Ø±Ø³Ø§Ù~D Ø§Ù~DØ±Ø³Ø§Ù~DØ©.

    (Ù~FØ¹ØªØ°Ø± Ø¥Ù~F Ù~DÙ~E ØªÙ~CÙ~F Ù~BØ¯ Ø·Ù~DØ¨Øª Ù~GØ°Ù~G Ø§Ù~DØ±Ø³Ø§Ù~DØ©. Ø¨Ù~EØ§ Ø£Ù~F Ø¨Ø±Ù~JØ¯Ù~C Ù~EÙ~BØ¯Ù~E Ù~EÙ~F
    Ø®Ø¯Ù~EØ© Ù~DØ§ØªØ³ØªØ®Ø¯Ù~E KDIMØ~L Ù~BÙ~EÙ~FØ§ Ø¨Ø¥Ø±Ø³Ø§Ù~D Ø´Ø±Ø­ Ù~EÙ~HØ¬Ø²Ø~L
    Ù~HØ³Ù~FØªØ¬Ø§Ù~GÙ~D Ø¹Ù~FÙ~HØ§Ù~F Ø§Ù~DØ¨Ø±Ù~JØ¯ Ù~GØ°Ø§ Ø®Ù~DØ§Ù~D Ø§Ù~DÙ~JÙ~HÙ~E Ø§Ù~DØªØ§Ù~DÙ~J ØªÙ~BØ±Ù~JØ¨Ø§Ù~K).

    Ù~JØ±Ø¬Ù~I Ù~EÙ~DØ§Ø­Ø¸Ø© Ø£Ù~FÙ~FØ§ Ù~DØ§ Ù~FØ³ØªØ·Ù~JØ¹ Ù~EØ¹Ø§Ù~DØ¬Ø© Ø±Ø³Ø§Ø¦Ù~D HTML Ø£Ù~H base 64
    . Ø³ØªØ­ØªØ§Ø¬ Ø£Ù~F ØªØ±Ø³Ù~D Ù~DÙ~FØ§ Ø±Ø³Ø§Ù~DØ© ØªØ­ØªÙ~HÙ~J Ø¹Ù~DÙ~I Ù~FØµ Ø¨Ø³Ù~JØ· Ù~AÙ~BØ·.

    Ø¥Ù~F Ù~CØ§Ù~FØª Ù~DØ¯Ù~JÙ~C Ø£Ø³Ø¦Ù~DØ© Ø£Ù~H Ø¥Ù~F Ù~DÙ~E Ù~JØ¹Ù~EÙ~D Ø§Ù~DØ­Ù~D Ù~JÙ~EÙ~CÙ~FÙ~C Ø§Ù~DØ§ØªØµØ§Ù~D Ø¨Ù~CØ§Ø¦Ù~F
    Ø¨Ø´Ø±Ù~J Ø¹Ù~DÙ~I Ø¹Ù~FÙ~HØ§Ù~F Ø§Ù~DØ¯Ø¹Ù~E Ø§Ù~DÙ~AÙ~FÙ~J Ù~GØ°Ø§: tor-assistants@torproject.org

    --

    Ø³Ù~DØ§Ù~E! Ø±Ù~HØ¨Ø§Øª "GetTor" Ø¯Ø± Ø®Ø¯Ù~EØª Ø´Ù~EØ§Ø³Øª. 
    Ù~EØªØ§Ø³Ù~AØ§Ù~FÙ~G Ù~EØ§ Ù~FÙ~EÛ~L ØªÙ~HØ§Ù~FÛ~LÙ~E Ø¨Ø§ Ø§Û~LÙ~F Ø¢Ø¯Ø±Ø³ Ø¨Ø§ Ø´Ù~EØ§ Ø¯Ø± Ø§Ø±ØªØ¨Ø§Ø· Ø¨Ø§Ø´Û~LÙ~E. Ø´Ù~EØ§ Ø¨Ø§Û~LØ³ØªÛ~L Ø¯Ø± 
    GMAIL.COM Û~LØ§ Ø¯Ø± YAHOO.CN Ø­Ø³Ø§Ø¨ Ø¨Ø§Ø² Ú©Ø±Ø¯Ù~G Ù~H Ø§Ø² Ø·Ø±Û~LÙ~B Û~LÚ©Û~L Ø§Ø² Ø¢Ù~F Ø¢Ø¯Ø±Ø³Ù~GØ§ Ø¨Ø§ Ù~EØ§ 
    Ù~EÚ©Ø§ØªØ¨Ù~G Ú©Ù~FÛ~LØ¯.
    
    Ù~EØ§ Ù~AÙ~BØ· Ø¯Ø±Ø®Ù~HØ§Ø³ØªÙ~GØ§Û~LÛ~L Ø±Ø§ Ù~EÙ~HØ±Ø¯ Ø¨Ø±Ø±Ø³Û~L Ù~BØ±Ø§Ø± Ù~EÛ~L Ø¯Ù~GÛ~LÙ~E Ú©Ù~G Ø³Ø±Ù~HÛ~LØ³ Ù¾Ø³Øª Ø§Ù~DÚ©ØªØ±Ù~HÙ~FÛ~LÚ©Û~L Ø¢Ù~FÙ~GØ§ 
    "DKIM" Ø±Ø§ Ù¾Ø´ØªÛ~LØ¨Ø§Ù~FÛ~L Ú©Ù~FØ¯. "DKIM" Ø§Û~LÙ~F Ø§Ù~EÚ©Ø§Ù~F Ø±Ø§ Ø¨Ù~G Ù~EØ§ Ù~EÛ~L Ø¯Ù~GØ¯ ØªØ§ Ø§Ø·Ù~EÛ~LÙ~FØ§Ù~F Û~LØ§Ø¨Û~LÙ~E Ú©Ù~G 
    Ø¢Ø¯Ø±Ø³ Ù~EÙ~FØ¯Ø±Ø¬ Ø¯Ø± Ù~BØ³Ù~EØª  "From"Ø~L Ù~GÙ~EØ§Ù~F Ø¢Ø¯Ø±Ø³Û~L Ø§Ø³Øª Ú©Ù~G Ù~FØ§Ù~EÙ~G Ø§Ø² Ø¢Ù~F Ø¨Ù~G Ù~EØ§ Ø§Ø±Ø³Ø§Ù~D Ø´Ø¯Ù~G 
    Ø§Ø³Øª. 
    
    (Ø¯Ø± Ù~GØ± ØµÙ~HØ±Øª Ø¹Ø°Ø±Ø®Ù~HØ§Ù~GÛ~L Ù~EØ§ Ø±Ø§ Ù¾Ø°Û~LØ±Ø§ Ø¨Ø§Ø´Û~LØ¯. Ø§Ø² Ø¢Ù~FØ¬Ø§Û~LÛ~LÚ©Ù~G Ø§Û~LÙ~EÛ~LÙ~D Ø´Ù~EØ§ DKIM Ø±Ø§ 
    Ù¾Ø´ØªÛ~LØ¨Ø§Ù~FÛ~L Ù~FÙ~EÛ~L Ú©Ù~FØ¯Ø~L Ù~EØ§ Ø§Û~LÙ~F ØªÙ~HØ¶Û~LØ­ Ú©Ù~HØªØ§Ù~G Ø±Ø§ Ø§Ø±Ø³Ø§Ù~D Ù~FÙ~EÙ~HØ¯Ù~G Ù~H Ø§Û~LÙ~F Ø¢Ø¯Ø±Ø³ Ø§Û~LÙ~EÛ~LÙ~D Ø±Ø§ 
    Ø¨Ø²Ù~HØ¯Û~L Ø§Ø² Ù~AÙ~GØ±Ø³Øª Ø¢Ø¯Ø±Ø³Ù~GØ§Û~L Ø®Ù~HØ¯ Ø®Ø§Ø±Ø¬ Ù~EÛ~L Ú©Ù~FÛ~LÙ~E.) 
    
    Ù~DØ·Ù~AØ§ Ø¨Ù~G Ø§Û~LÙ~F Ù~FÚ©ØªÙ~G ØªÙ~HØ¬Ù~G Ø¯Ø§Ø´ØªÙ~G Ø¨Ø§Ø´Û~LØ¯ Ú©Ù~G Ø¯Ø± Ø­Ø§Ù~D Ø­Ø§Ø¶Ø± Ø§Û~LÙ~EÛ~LÙ~D Ù~GØ§Û~L Ù~EØ¨ØªÙ~FÛ~L Ø¨Ø± HTML Û~LØ§ 
    64 Ø¨Û~LØªÛ~LØ~L Ù~BØ§Ø¨Ù~D Ø¨Ø±Ø±Ø³Û~L Ù~FÙ~EÛ~L Ø¨Ø§Ø´Ù~FØ¯. Ø¨Ù~FØ§Ø¨Ø±Ø§Û~LÙ~F Ø§Û~LÙ~EÛ~LÙ~D Ù~GØ§Û~L Ø®Ù~HØ¯ Ø±Ø§ Ø¨Ù~G ØµÙ~HØ±Øª Ù~EØªÙ~F Ø³Ø§Ø¯Ù~G 
    Ø§Ø±Ø³Ø§Ù~D Ù~FÙ~EØ§Û~LÛ~LØ¯. 
    
    Ú~FÙ~FØ§Ù~FÚ~FÙ~G Ø³Ù~HØ§Ù~DÛ~L Ø¯Ø§Ø±Û~LØ¯ Û~LØ§ Ø¨Ø±Ù~FØ§Ù~EÙ~G Ø¯Ú~FØ§Ø± Ø§Ø´Ú©Ø§Ù~D Ø¨Ù~HØ¯Ù~G Ù~H Ú©Ø§Ø± Ù~FÙ~EÛ~L Ú©Ù~FØ¯ Ø~L Ø¨Ø§ Ù~BØ³Ù~EØª 
    Ù¾Ø´ØªÛ~LØ¨Ø§Ù~FÛ~L Ø¨Ø§ Ø¢Ø¯Ø±Ø³ Ø²Û~LØ± ØªÙ~EØ§Ø³ Ø¨Ú¯Û~LØ±Û~LØ¯ ØªØ§ Û~LÚ© Ø§Ù~FØ³Ø§Ù~F Ø¨Ù~G Ø³Ù~HØ§Ù~D Ø´Ù~EØ§ Ù¾Ø§Ø³Ø® Ø¯Ù~GØ¯:
    tor-assistants@torproject.org

    --

    OlÃ¡! Este Ã© o robot "GetTor".
    
    Infelizmente, nÃ£o respondemos neste endereÃ§o, pelo que Ã©
    recomendado criar uma conta no Gmail ou Hotmail e enviar a mensagem de um 
    desses serviÃ§os.
    
    SÃ³ processamos emails de serviÃ§os que suportam "DKIM",
    que Ã© uma forma de verificar que o endereÃ§o do "Remetente" Ã© vÃ¡lido e se foi 
    mesmo esse a enviar o email.
    
    (Pedimos desculpa se nÃ£o solicitou este email. Como a sua mensagem Ã© de um 
    serviÃ§o que nÃ£o suporta  DKIM, estamos a enviar esta curta explicaÃ§Ã£o, e 
    depois este endereÃ§o de email serÃ¡ ignorado.)
    
    Actualmente nÃ£o suportamos emails com HTML or Base64, pelo que terÃ¡ que 
    utilizar apenas texto (plain text).
    
    Se tiver alguma dÃºvida, pode contactar um humano no seguinte endereÃ§o: 
    tor-assistants@torproject.org

    --

    Ð~WÐ´Ñ~@Ð°Ð²Ñ~AÑ~BÐ²Ñ~CÐ¹Ñ~BÐµ! Ð­Ñ~BÐ¾ "Ñ~@Ð¾Ð±Ð¾Ñ~B GetTor".
    
    Ð~Z Ñ~AÐ¾Ð¶Ð°Ð»ÐµÐ½Ð¸Ñ~N, Ð¼Ñ~K Ð½Ðµ Ñ~AÐ¼Ð¾Ð¶ÐµÐ¼ Ð¾Ñ~BÐ²ÐµÑ~BÐ¸Ñ~BÑ~L Ð²Ð°Ð¼ Ð½Ð° Ñ~MÑ~BÐ¾Ñ~B Ð°Ð´Ñ~@ÐµÑ~A. Ð~RÑ~K Ð´Ð¾Ð»Ð¶Ð½Ñ~K Ñ~AÐ¾Ð·Ð´Ð°Ñ~BÑ~L
       Ñ~AÑ~GÐµÑ~B Ð² GMAIL.COM Ð¸Ð»Ð¸ Ð² YAHOO.COM Ð¸ Ð¾Ñ~BÐ¿Ñ~@Ð°Ð²Ð»Ñ~OÑ~BÑ~L Ð¿Ð¾Ñ~GÑ~BÑ~C Ð¸Ð· 
        Ð¾Ð´Ð½Ð¾Ð³Ð¾ Ð¸Ð· Ñ~MÑ~BÐ¸Ñ~E Ñ~AÑ~GÐµÑ~BÐ¾Ð².
    
    Ð~\Ñ~K Ñ~BÐ¾Ð»Ñ~LÐºÐ¾ Ð¾Ð±Ñ~@Ð°Ð±Ð°Ñ~BÑ~KÐ²Ð°ÐµÐ¼ Ð·Ð°Ð¿Ñ~@Ð¾Ñ~AÑ~K Ð¸Ð· Ð¿Ð¾Ñ~GÑ~BÐ¾Ð²Ñ~KÑ~E Ñ~AÐ»Ñ~CÐ¶Ð± Ð¿Ð¾Ð´Ð´ÐµÑ~@Ð¶Ð¸Ð²Ð°Ñ~NÑ~IÐ¸Ñ~E "DKIM",
    ÐºÐ¾Ñ~BÐ¾Ñ~@Ð°Ñ~O Ñ~OÐ²Ð»Ñ~OÐµÑ~BÑ~AÑ~O Ñ~DÑ~CÐ½ÐºÑ~FÐ¸ÐµÐ¹ Ñ~MÐ»ÐµÐºÑ~BÑ~@Ð¾Ð½Ð½Ð¾Ð¹ Ð¿Ð¾Ñ~GÑ~BÑ~K, Ð¿Ð¾Ð·Ð²Ð¾Ð»Ñ~OÑ~NÑ~IÐ°Ñ~O Ð½Ð°Ð¼ Ñ~CÐ±ÐµÐ´Ð¸Ñ~BÑ~LÑ~AÑ~O Ð² 
    Ñ~BÐ¾Ð¼, Ñ~GÑ~BÐ¾ Ð°Ð´Ñ~@ÐµÑ~A Ð²
    Ñ~AÑ~BÑ~@Ð¾ÐºÐµ "Ð~^Ñ~B" Ð´ÐµÐ¹Ñ~AÑ~BÐ²Ð¸Ñ~BÐµÐ»Ñ~LÐ½Ð¾ Ð¾Ñ~B Ñ~BÐ¾Ð³Ð¾, ÐºÑ~BÐ¾ Ð¾Ñ~BÐ¾Ñ~AÐ»Ð°Ð» Ð¿Ð¾Ñ~GÑ~BÑ~C.
    
     (Ð~\Ñ~K Ð¿Ñ~@Ð¸Ð½Ð¾Ñ~AÐ¸Ð¼ Ð¸Ð·Ð²Ð¸Ð½ÐµÐ½Ð¸Ñ~O, ÐµÑ~AÐ»Ð¸ Ð²Ñ~K Ð½Ðµ Ð¿Ñ~@Ð¾Ñ~AÐ¸Ð»Ð¸ Ñ~MÑ~BÐ¾Ð³Ð¾ Ð¿Ð¸Ñ~AÑ~LÐ¼Ð°. Ð¢Ð°Ðº ÐºÐ°Ðº Ð²Ð°Ñ~HÐµ  
    email Ð¸Ð· Ñ~AÐµÑ~@Ð²Ð¸Ñ~AÐ°
    ÐºÐ¾Ñ~BÐ¾Ñ~@Ñ~KÐ¹ Ð½Ðµ Ð¸Ñ~AÐ¿Ð¾Ð»Ñ~LÐ·Ñ~CÐµÑ~B DKIM, Ð¼Ñ~K Ð¾Ñ~BÐ¿Ñ~@Ð°Ð²Ð»Ñ~OÐµÐ¼ ÐºÑ~@Ð°Ñ~BÐºÐ¾Ðµ Ð¾Ð±Ñ~JÑ~OÑ~AÐ½ÐµÐ½Ð¸Ðµ,
    Ð¸ Ð´Ð°Ð»ÐµÐµ Ð¼Ñ~K Ð¿Ñ~@Ð¾Ð¸Ð³Ð½Ð¾Ñ~@Ð¸Ñ~@Ñ~CÐµÐ¼ Ñ~MÑ~BÐ¾Ñ~B Ð°Ð´Ñ~@ÐµÑ~A Ñ~MÐ»ÐµÐºÑ~BÑ~@Ð¾Ð½Ð½Ð¾Ð¹ Ð¿Ð¾Ñ~GÑ~BÑ~K Ð´ÐµÐ½Ñ~L Ð¸Ð»Ð¸ Ð´Ð²Ð°.)
    
    Ð~_Ð¾Ð¶Ð°Ð»Ñ~CÐ¹Ñ~AÑ~BÐ° Ð¾Ñ~BÐ¼ÐµÑ~BÑ~LÑ~BÐµ, Ñ~GÑ~BÐ¾ Ð² Ð½Ð°Ñ~AÑ~BÐ¾Ñ~OÑ~IÐµÐµ Ð²Ñ~@ÐµÐ¼Ñ~O Ð¼Ñ~K Ð½Ðµ Ð¼Ð¾Ð¶ÐµÐ¼ Ð¾Ð±Ñ~@Ð°Ð±Ð¾Ñ~BÐ°Ñ~BÑ~L HTML 
    Ð¿Ð¸Ñ~AÑ~LÐ¼Ð° Ð¸Ð»Ð¸ Ð±Ð°Ð·Ð¾Ð²Ñ~KÐµ 64
    Ð¿Ð¾Ñ~GÑ~BÑ~C. Ð~RÑ~K Ð´Ð¾Ð»Ð¶Ð½Ñ~K Ð±Ñ~CÐ´ÐµÑ~BÐµ Ð¿Ð¾Ñ~AÐ»Ð°Ñ~BÑ~L Ð¾Ð±Ñ~KÑ~GÐ½Ñ~KÐ¹ Ñ~BÐµÐºÑ~AÑ~B (plain text).
    
    Ð~UÑ~AÐ»Ð¸ Ñ~C Ð²Ð°Ñ~A Ð²Ð¾Ð¿Ñ~@Ð¾Ñ~AÑ~K Ð¸Ð»Ð¸ Ñ~GÑ~BÐ¾ Ñ~BÐ¾ Ð½Ðµ Ñ~AÑ~@Ð°Ð±Ð¾Ñ~BÐ°Ð»Ð¾, Ð²Ñ~K Ð¼Ð¾Ð¶ÐµÑ~BÐµ Ñ~AÐ²Ñ~OÐ·Ð°Ñ~BÑ~LÑ~AÑ~O 
    Ñ~A Ð¶Ð¸Ð²Ñ~KÐ¼ Ð¿Ñ~@ÐµÐ´Ñ~AÑ~BÐ°Ð²Ð¸Ñ~BÐµÐ»ÐµÐ¼ Ð¿Ð¾ Ñ~MÑ~BÐ¾Ð¼Ñ~C Ñ~MÐ»ÐµÐºÑ~BÑ~@Ð¾Ð½Ð½Ð¾Ð¼Ñ~C Ð°Ð´Ñ~@ÐµÑ~AÑ~C:tor-assistants@torproject.org

    --

       ä½| å¥½!è¿~Yé~G~Læ~X¯â~@~\GetTorâ~@~]è~Gªå~J¨å~[~^å¤~Mã~@~B

       å¾~Hæ~J±æ­~Iï¼~Læ~H~Qä»¬ä¸~Må¯¹è¿~Yä¸ªå~\°å~]~@è¿~[è¡~Lå~[~^å¤~Mï¼~Læ~B¨åº~Té~@~Zè¿~G
       GMAIL.COMæ~H~Vyahoo.cnç~Z~Dè´¦æ~H·ä½¿ç~T¨æ~H~Qä»¬ç~Z~Dæ~\~Må~J¡ã~@~B

       æ~H~Qä»¬è¦~Aæ±~Bæ~I~@å¤~Dç~P~Fé~B®ä»¶è¯·æ±~Bç~Z~Dç~Tµé~B®æ~\~Må~J¡å~U~Få¿~Eé¡»æ~T¯æ~L~Aâ~@~\DKIMâ~@~]
       å®~Cå¸®å~J©æ~H~Qä»¬éª~Lè¯~Aé~B®ä»¶æ~X¯å~P¦ç~\~_ç~Z~Dæ~]¥è~Gªäº~Næ~B¨ç~Z~Dé~B®ç®±ã~@~B

       (å¦~Bæ~^~\æ~B¨æ²¡æ~\~Iå~P~Qæ~H~Qä»¬å~O~Qé~@~Aè¿~Gé~B®ä»¶è¯·æ±~Bï¼~Lå¯¹æ­¤å~[~^å¤~Mæ~H~Qä»¬å¾~Hæ~J±æ­~Iã~@~B
      å~[| ä¸ºæ~B¨ç~Z~Dé~B®ä»¶æ~\~Må~J¡å~U~Fä¸~Mæ~O~Pä¾~[DKIMå~J~_è~C½ï¼~Læ~\~Iäººå~O¯è~C½ä¼ªé~@| äº~Fä½| é~B®å~]~@
      æ~H~Qä»¬è¿~Yé~G~Lå~O~Qé~@~Aä¸~@æ~]¡ç®~@ç~_­ç~Z~Dé~@~Zç~_¥ï¼~Lå¹¶å°~Få~\¨ä»¥å~P~Nç~Z~Då~G| å¤©é~G~Lå¿½ç~U¥è¯¥é~B®å~]~@ï¼~L
      ä»¥å~E~Må½¢æ~H~På~^~Cå~\¾å~[~^å¤~Mã~@~B)

       è¯·æ³¨æ~D~Oï¼~Læ~H~Qä»¬ç~[®å~I~Mæ~W| æ³~Uå¤~Dç~P~FHTMLæ~H~VBase64ç¼~Vç| ~Aç~Z~Dé~B®ä»¶ï¼~Læ~B¨å~Oªè~C½å~O~Qé~@~Açº¯æ~V~Gæ~\¬è¯·æ±~Bã~@~B

       å¦~Bæ~^~\æ~B¨é~A~Gå~H°ä»»ä½~Ué~W®é¢~Xè¯·è~A~Tç³»æ~H~Qä»¬ç~Z~Dæ~J~@æ~\¯æ~T¯æ~L~Aé~B®ç®±ï¼~Z
         tor-assistants@torproject.org
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
obtain_locallized_underline = """
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


