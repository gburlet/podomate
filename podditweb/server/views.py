import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from server.models import License, Activation, AppVersion
from server.serializers import LatestAppVersionSerializer


def index(request):
    return HttpResponse("Hello, poddit.")


def guide(request):
    return HttpResponse("Guide to using poddit")


class ClientVersion(APIView):
    """
    Endpoint for client to check whether version is sunsetted (refuse access to app)

    GET
    params:
        sku (string): product sku
        version (string): client version
    returns:
        200 if active, 400 if sunsetted

    Test GET:
        curl "http://localhost:8001/api/version?sku=poddit-desktop&version=0.1.21"
    """

    def get(self, request):
        err_data = {}
        required_fields = {"sku", "version"}
        for rf in required_fields:
            if request.query_params.get(rf) is None or request.data.get(rf) == "":
                err_data[rf] = "Required field"

        # if we're missing (meta)data or it is invalid. Escape immediately.
        if len(err_data):
            return Response(err_data, status.HTTP_400_BAD_REQUEST)

        try:
            app_version = AppVersion.objects.get(product__sku=request.query_params.get("sku"), version=request.query_params.get("version"))
            from django.utils import timezone
            if app_version.sunset_date is not None and app_version.sunset_date < timezone.now():
                return Response({"error": "Update required"}, status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_200_OK)
        except AppVersion.DoesNotExist:
            return Response({"error": "App version is not valid"}, status.HTTP_400_BAD_REQUEST)


class Update(APIView):
    """
    Endpoint for client to check for app updates

    GET
    params:
        sku (string): product sku
    returns:
        sku (string): product sku
        version (string): latest version
        mac_link (string): link to download newest mac app
        windows_link (string): link to download newest windows app

    Test GET:
        curl "http://localhost:8001/api/update?sku=poddit-desktop"
    """

    def get(self, request):
        err_data = {}
        required_fields = {"sku"}
        for rf in required_fields:
            if request.query_params.get(rf) is None or request.data.get(rf) == "":
                err_data[rf] = "Required field"

        # if we're missing (meta)data or it is invalid. Escape immediately.
        if len(err_data):
            return Response(err_data, status.HTTP_400_BAD_REQUEST)

        latest_app_version = AppVersion.objects.filter(product__sku=request.query_params.get("sku")).order_by("-release_date")[0]
        return Response(LatestAppVersionSerializer(latest_app_version, context={"request": request}).data)


class Activate(APIView):
    """
    Activate the license on a specific computer

    POST
    params:
        email (string): email entered by user
        key (string): license key entered by user
        mac (string): MAC address obtained from client machine
    returns:
        signed_response

    Test POST:
        curl -X POST http://localhost:8001/api/activate -F email='gregory.burlet@gmail.com' -F license_key='3D319CDD-5B1D-573C-B92C-F3BF231EBD68' -F mac_address='8c:85:90:3e:5e:d9'
    """

    def post(self, request):
        err_data = {}
        required_fields = {"email", "license_key", "mac_address"}

        for rf in required_fields:
            if request.data.get(rf) is None or request.data.get(rf) == "":
                err_data[rf] = "Required field"

        # if we're missing (meta)data or it is invalid. Escape immediately.
        if len(err_data):
            return Response(err_data, status.HTTP_400_BAD_REQUEST)

        email = request.data["email"]
        license_key = request.data["license_key"]
        mac_address = request.data["mac_address"]

        # check license exists
        try:
            license = License.objects.get(user__email=email, key=license_key)
        except License.DoesNotExist:
            return Response({"general": "Invalid license key"}, status.HTTP_403_FORBIDDEN)

        # check already activated and create new activation if necessary
        try:
            activation = Activation.objects.get(license=license, mac=mac_address)
        except Activation.DoesNotExist:
            if license.activations_remaining > 0:
                activation = Activation(license=license, mac=mac_address)
                activation.save()
            else:
                return Response(
                    {"general": "The license key has been activated too many times"},
                    status.HTTP_403_FORBIDDEN
                )

        # return activation data to client and sign using RSA
        private_key_path = os.path.join(os.path.dirname(__file__), "poddit_private.pem")
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )

        message = activation.mac
        signature = private_key.sign(
            bytes(message, encoding='utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # base64 encode encrypted binary to human-readable string
        encoded_signature = base64.b64encode(signature).decode('utf-8')

        return Response(
            {"activations_remaining": license.activations_remaining, "signature": encoded_signature},
            status.HTTP_200_OK
        )
