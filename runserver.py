# -*- coding:utf-8 -*-
#
# Author: promisejohn
# Email: promise.john@gmail.com
#

from compusher import app
# app.config.update(DEBUG=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
    # app.run()
