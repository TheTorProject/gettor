#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gettor.http


def main():
    api = gettor.http.HTTP('http.cfg')
    api.load_data()
    api.run()

if __name__ == '__main__':
    main()
