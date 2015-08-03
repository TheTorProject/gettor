#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

import gettor.smtp

def main():
    logging_level = 'INFO'
    logging_file = '/path/to/gettor/log/process_email.log'
    logging_format = '[%(levelname)s] %(asctime)s - %(message)s'
    date_format = "%Y-%m-%d" # %H:%M:%S

    logging.basicConfig(
        format=logging_format,
        datefmt=date_format,
        filename = logging_file,
        level = logging_level
    )

    logging.debug("New email received")
    logging.debug("Creating new SMTP object")
    
    try:
        service = gettor.smtp.SMTP('/path/to/gettor/smtp.cfg')
        incoming = sys.stdin.read()
        service.process_email(incoming)
        logging.debug("Email processed sucessfully")
    except gettor.smtp.ConfigError as e:
        logging.error("Configuration error: %s" % str(e))        
    except gettor.smtp.SendEmailError as e:
        logging.error("SMTP not working: %s" % str(e))
    except gettor.smtp.InternalError as e:
        logging.error("Core module not working: %s" % str(e))
    except Exception as e:
        # in case something unexpected happens
        logging.critical("Unexpected error: %s" % str(e))

if __name__ == '__main__':
    main()
