import threading
import asyncio
import time

from odoo import models, fields, api

from ..common.we_request import WeRequest


class App(models.Model):
    _name = 'wechat.enterprise.app'
    _description = 'Wechat Enterprise App'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    corp_id = fields.Char(string='Corp ID', required=True)
    corp_secret = fields.Char(string='Corp Secret', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)

    def run_sync(self):
        # create a threading to avoid odoo ui blocking
        def _sync():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(loop.create_task(self.sync_organization()))
            loop.close()

        thread = threading.Thread(target=_sync)
        thread.start()

    async def sync_organization(self):
        uid = self.env.uid
        start_time = time.time()
        with self.env.registry.cursor() as new_cr:
            self.env = api.Environment(new_cr, uid, {})
            we_request = WeRequest(self.corp_id, self.corp_secret)
            departments = await we_request.department_simplelist()
            print(departments)
            tasks = []
            for dep in departments:
                tasks.append(self.env['hr.department'].sync_department(we_request, self, dep))

            res = await asyncio.gather(*tasks)
            print(res)
            print('finish sync')
            print(time.time() - start_time)

