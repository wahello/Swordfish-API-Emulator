#
# Copyright (c) 2017-2021, The Storage Networking Industry Association.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of The Storage Networking Industry Association (SNIA) nor
# the names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#  THE POSSIBILITY OF SUCH DAMAGE.
#
# volumes_api.py


import json, os
import traceback
import logging
import g
import urllib3
import shutil

from flask import jsonify, request
from flask_restful import Resource
from api_emulator.utils import update_collections_json, create_path, get_json_data, create_and_patch_object, delete_object, patch_object, put_object, delete_collection, create_collection
from .constants import *
from .templates.volumes import get_Volumes_instance


members =[]
member_ids = []
config = {}
INTERNAL_ERROR = 500

# VolumesAPI API
class VolumesAPI(Resource):
    def __init__(self, **kwargs):
        logging.info('VolumesAPI init called')
        self.root = PATHS['Root']
        self.storage = PATHS['Storage']['path']
        self.volumes = PATHS['Storage']['volume']

    # HTTP GET
    def get(self, storage, volume):
        path = create_path(self.root, self.storage, storage, self.volumes, volume, 'index.json')
        return get_json_data (path)

    # HTTP POST
    # - Create the resource (since URI variables are available)
    # - Update the members and members.id lists
    # - Attach the APIs of subordinate resources (do this only once)
    # - Finally, create an instance of the subordinate resources
    def post(self, storage, volume):
        logging.info('VolumesAPI POST called')
        path = create_path(self.root, self.storage, storage, self.volumes, volume)
        collection_path = os.path.join(self.root, self.storage, storage, self.volumes, 'index.json')

        # Check if collection exists:
        if not os.path.exists(collection_path):
            VolumesCollectionAPI.post (self, storage)

        if volume in members:
            resp = 404
            return resp
        try:
            global config
            wildcards = {'s_id':storage, 'v_id': volume, 'rb': g.rest_base}
            config=get_Volumes_instance(wildcards)
            config = create_and_patch_object (config, members, member_ids, path, collection_path)
            resp = config, 200

        except Exception:
            traceback.print_exc()
            resp = INTERNAL_ERROR
        logging.info('VolumesAPI POST exit')
        return resp

	# HTTP PATCH
    def patch(self, storage, volume):
        path = os.path.join(self.root, self.storage, volume, self.volumes, volume, 'index.json')
        patch_object(path)
        return self.get(storage, volume)

	# HTTP PUT
    def put(self, storage, volume):
        path = os.path.join(self.root, self.storage, volume, self.volumes, volume, 'index.json')
        put_object(path)
        return self.get(storage, volume)

    # HTTP DELETE
    def delete(self, storage, volume):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.storage, volume, self.volumes, volume)
        base_path = create_path(self.root, self.storage, volume, self.volumes)
        return delete_object(path, base_path)

# Volumes Collection API
class VolumesCollectionAPI(Resource):

    def __init__(self):
        self.root = PATHS['Root']
        self.storage = PATHS['Storage']['path']
        self.volumes = PATHS['Storage']['volumes']

    def get(self, storage):
        path = os.path.join(self.root, self.storage, storage, self.volumes, 'index.json')
        return get_json_data (path)

    def verify(self, config):
        # TODO: Implement a method to verify that the POST body is valid
        return True,{}

    # HTTP POST Collection
    def post(self, volume):
        self.root = PATHS['Root']
        self.storage = PATHS['Storage']['path']
        self.volumes = PATHS['Storage']['volume']

        logging.info('VolumesCollectionAPI POST called')

        if volume in members:
            resp = 404
            return resp

        path = create_path(self.root, self.storage, volume, self.volumes)
        return create_collection (path, 'Volume')

    # HTTP PUT
    def put(self, volume):
        path = os.path.join(self.root, self.storage, volume, self.volumes, 'index.json')
        put_object(path)
        return self.get(volume)

    # HTTP DELETE
    def delete(self, volume):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.storage, volume, self.volumes)
        base_path = create_path(self.root, self.storage)
        return delete_collection(path, base_path)

class CreateVolume (Resource):
    def __init__(self):
        self.root = PATHS['Root']
        self.storage = PATHS['Storage']['path']
        self.volumes = PATHS['Storage']['volumes']

    # Attach APIs for subordinate resource(s). Attach the APIs for a resource collection and its singletons
    def put(self,storage):
        logging.info('CreateVolume put started.')
        try:
            path = create_path(self.root, self.storage, storage, self.volumes)
            if not os.path.exists(path):
                os.mkdir(path)
            else:
                logging.info('The given path : {} already Exist.'.format(path))
            config={
                      "@Redfish.Copyright": "Copyright 2015-2021 SNIA. All rights reserved.",
                      "@odata.id": "/redfish/v1/Storage/$metadata#/Volumes",
                      "@odata.type": "#VolumeCollection.VolumeCollection",
                      "Name": "Volume Collection",
                      "Members@odata.count": 0,
                      "Members": [
                      ],
                      "Permissions": [
                                {"Read": "True"},
                                {"Write": "True"}]
                    }
            with open(os.path.join(path, "index.json"), "w") as fd:
                fd.write(json.dumps(config, indent=4, sort_keys=True))

            resp = config, 200
        except Exception:
            traceback.print_exc()
            resp = INTERNAL_ERROR
        logging.info('CreateVolume put exit.')
        return resp
