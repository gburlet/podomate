from rest_framework import serializers

from podomateweb import settings
from server.models import AppVersion


class LatestAppVersionSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="product.sku")
    mac_link = serializers.SerializerMethodField()
    windows_link = serializers.SerializerMethodField()

    class Meta:
        model = AppVersion
        fields = ('sku', 'version', 'mac_link', 'windows_link')

    def _get_link_root(self):
        request = self.context["request"]

        if settings.USE_S3:
            return settings.STATIC_URL + "server/versions/"
        else:
            # for local dev
            return '{scheme}://{host}{static_url}server/versions/'.format(
                scheme=request.scheme, host=request.get_host(), static_url=settings.STATIC_URL
            )

    def get_mac_link(self, app_version):
        return self._get_link_root() + '%s/%s/Podomate.app.zip' % (app_version.product.sku, app_version.version)

    def get_windows_link(self, app_version):
        return self._get_link_root() + '%s/%s/Podomate.exe.zip' % (app_version.product.sku, app_version.version)
