from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'API接口'

    def ready(self):
        """
        应用启动时执行
        可以在这里进行一些初始化操作
        """
        try:
            # 可以在这里创建默认的网站信息
            from .models import WebsiteInfo
            if not WebsiteInfo.objects.exists():
                WebsiteInfo.objects.create(
                    title="图书管理系统",
                    content="欢迎使用智能图书管理系统！本系统提供便捷的图书借阅、查询和管理功能。"
                )
                print("默认网站信息已创建")
        except Exception as e:
            # 在首次迁移时可能会报错，这是正常的
            pass