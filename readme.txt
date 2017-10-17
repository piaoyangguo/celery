Python组件：
1. python2.7
2. Django1.7.1
3. celery( amqp-1.4.9 anyjson-0.3.3 billiard-3.3.0.22 celery-3.1.20 )    #使用pip install celery会自定把这些都装上，默认安装符合依赖的最新版。
4. django-celery-3.1.17    #还是用pip装，这个是用来支持结果写入数据库的。


1. 新建django project：
django-admin startproject django_celery
cd django_celery
django-admin startapp demoapp

2. 新建celery配置：（详情看文末的解释）
django_celery/django_celery/celery.py：
[python] view plain copy print?
from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_celery.settings')

app = Celery('django_celery')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


3. 设置导入celery实例：
修改django_celery/django_celery/__init__.py：
[python] view plain copy print?
from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

4. 新建demo tasks：
django_celery/demoapp/tasks.py：
[python] view plain copy print?
from __future__ import absolute_import
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

5. 修改项目配置：
一、django_celery/django_celery/settings.py：
1）【可选】屏蔽不需要的app：admin、auth、contenttypes、sessions、messages、staticfiles。
2）增加app：'demoapp','djcelery','kombu.transport.django', ：
[python] view plain copy print?
INSTALLED_APPS = (
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django.contrib.messages',
    # 'django.contrib.staticfiles',
    'demoapp',
    'djcelery',
    'kombu.transport.django',
)

3）增加 broker 配置：
[python] view plain copy print?
BROKER_URL = 'django://localhost:8000//'



执行命令进行测试：
python manage.py syncdb                      #同步数据库，仅首次运行
python managepy runserver                    #运行站点，默认端口8000
【新终端/命令行】
python manage.py celery worker -l info        #开启celery worker 进程
【另一个新终端/命令行】
python manage.py shell
>>> from demoapp.tasks import *
>>> dir()
['__builtins__', 'absolute_import', 'add', 'mul', 'shared_task', 'xsum']
>>> mul(5,2)          #可以看到，直接执行命令是没有问题的，直接返回。
10
>>> mul.delay(5,2)       #采用delay方式执行，会发送任务到worker
<AsyncResult: 2922623d-e89b-48c1-a355-bc8d566d10e7>
>>> add.delay(2,3)
<AsyncResult: e07aea9b-86da-4d84-89c7-768aca076b53>

运行结果（在worker终端/命令行中查看）：
[2016-01-27 17:58:56,418: INFO/MainProcess] Received task: demoapp.tasks.mul[2922623d-e89b-48c1-a355-bc8d566d10e7]
[2016-01-27 17:58:56,437: INFO/MainProcess] Task demoapp.tasks.mul[2922623d-e89b-48c1-a355-bc8d566d10e7] succeeded in 0.0169999599457s: 10
[2016-01-27 18:00:46,618: INFO/MainProcess] Received task: demoapp.tasks.add[e07aea9b-86da-4d84-89c7-768aca076b53]
[2016-01-27 18:00:46,630: INFO/MainProcess] Task demoapp.tasks.add[e07aea9b-86da-4d84-89c7-768aca076b53] succeeded in 0.0100002288818s: 5

至此，demo结束。

【此部分内容仅研究使用，时间较忙无需关心】
1. 下面讲解一下celery.py文件的配置内容，为何要这么配置。
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_celery.settings') 设置这个环境变量是为了让 celery 命令能找到 Django 项目。这条语句必须出现在 Celery 实例创建之前。
app = Celery('django_celery') 这个 app 就是 Celery 实例。可以有很多 Celery 实例，但是当使用 Django 时，似乎没有必要。
app.config_from_object('django.conf:settings')
可以将 settings 对象作为参数传入，但是更好的方式是使用字符串，因为当使用 Windows 系统或者 execv 时 celery worker 不需要序列化 settings 对象。
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
为了重用 Django APP，通常是在单独的 tasks.py 模块中定义所有任务。Celery 会自动发现这些模块，加上这一句后，Celery 会自动发现 Django APP 中定义的任务，前提是遵循如下 tasks.py 约定：
- app1/
    - tasks.py
    - models.py
- app2/
    - tasks.py
    - models.py

2. 关于broker：
这个是个什么东西，我还是不太理解，按照seeting的配置来说，我理解就是承载的站点。
BROKER_URL = 'django://localhost:8000//'
这里要注意我是使用了django自带的broker来作为celery broker，传说可以选的broker有：
RabbitMQ
Redis
database
更多的内容可以参看参考文献2。

# views.py

from app.tasks import add,sendmail

def task_workorder(request, id):
    """任务添加"""
    # ......你的代码......
    sendmail.delay(dict(to='asd@as.com'))  #申请人提交后会给审批人发邮件
    # ......你的代码......

注意：如果执行成功，你运行celery -A app.tasks worker –loglevel=info命令的终端会打印一些内容；如果执行失败，报一大把红色代码。。。那么恭喜你！出错了！这种错误，一般都是与你传的参数相关，尤其在django框架下，不要将queryset这种数据查询结果直接传递。