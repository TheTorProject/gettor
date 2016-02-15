#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gettor.http2


def main():
    api = gettor.http2.HTTP('http.cfg')
    api.load_data()
    # api.run()
    api.build()

if __name__ == '__main__':
    main()
