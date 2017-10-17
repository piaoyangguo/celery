from __future__ import absolute_import
from celery.task import task
import time
from celery import shared_task

@shared_task
def add(x, y):
    return x + y

@shared_task
def mul(x, y):
    return x * y

@shared_task
def xsum(numbers):
    return sum(numbers)

@task
def sendmail(mail):
    print "++++++++++++++++++++++++++++++++++++"
    print('sending mail to %s...' % mail['to'])
    time.sleep(2.0)
    print('mail sent.')
    print "------------------------------------"
    return mail['to']


@shared_task
def test():
    print "+++++++++++++++"
    print "-------------="
    return "success"