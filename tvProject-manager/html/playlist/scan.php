<?php

require_once('../getID3/getid3/getid3.php');
require_once '../getID3/getid3/extension.cache.mysqli.php';
$getID3 = new getID3;
$getID3 = new getID3_cached_mysqli('localhost', 'getid3', 'root', 'root');
$getID3->encoding = 'UTF-8';


$iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator('/var/www/html/playlist/Network/Activities/'));
foreach ($iterator as $file) {
	if ($file->isDir()) continue;
	$path = $file->getPathname();
	
	$file_meta = $getID3->analyze($path);	
	echo $path."<br />";
	ob_flush();
	flush();

}

?>
