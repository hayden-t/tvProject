<?php

require(dirname(__FILE__).'/../../../autoload.php');

use jalder\Upnp\Mediaserver;

$mediaserver = new Mediaserver();

$server = json_decode('{
    "location": "http://192.168.60.250:50001/desc/device.xml",
    "description": {
      "device": {
        "serviceList": {
          "service": [
            { 
              "serviceId": "urn:upnp-org:serviceId:ContentDirectory",
              "controlURL": "/ContentDirectory/control"
            }
          ]
        }
      }
    }
  }
',true);


    $browse = new Mediaserver\Browse($server);
    $directories = $browse->browse('23$3674', 'BrowseDirectChildren');


	echo     "<pre>";
	print_r($directories);
	echo "</pre>";

