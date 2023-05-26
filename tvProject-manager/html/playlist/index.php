<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
/********************************
Simple PHP File Manager
Copyright John Campbell (jcampbell1)

Liscense: MIT
********************************/

//Disable error report for undefined superglobals

require_once('../config.php');

$video_extensions = ['mkv','avi','mpg','mpeg','mov','mp4'];

require_once('../getID3/getid3/getid3.php');
//require_once '../getID3/getid3/extension.cache.mysqli.php';
$getID3 = new getID3;
//$getID3 = new getID3_cached_mysqli('localhost', 'getid3', 'root', 'root');
$getID3->encoding = 'UTF-8';


//Security options
$allow_delete = true; // Set to false to disable delete button and delete POST request.
$allow_upload = true; // Set to true to allow upload files
$allow_create_folder = true; // Set to false to disable folder creation
$allow_direct_link = true; // Set to false to only allow downloads and not direct link
$allow_show_folders = true; // Set to false to hide all subdirectories

$disallowed_patterns = ['*.php'];  // must be an array.  Matching files not allowed to be uploaded
$hidden_patterns = ['*.php','.*']; // Matching files hidden in directory index

$PASSWORD = '';  // Set the password, to access the file manager... (optional)

if($PASSWORD) {

	session_start();
	if(!$_SESSION['_sfm_allowed']) {
		// sha1, and random bytes to thwart timing attacks.  Not meant as secure hashing.
		$t = bin2hex(openssl_random_pseudo_bytes(10));
		if($_POST['p'] && sha1($t.$_POST['p']) === sha1($t.$PASSWORD)) {
			$_SESSION['_sfm_allowed'] = true;
			header('Location: ?');
		}
		echo '<html><body><form action=? method=post>PASSWORD:<input type=password name=p autofocus/></form></body></html>';
		exit;
	}
}

// must be in UTF-8 or `basename` doesn't work
setlocale(LC_ALL,'en_US.UTF-8');

$requestFile = (isset($_REQUEST['file']) ? $_REQUEST['file'] : '');
$getDo = (isset($_GET['do']) ? $_GET['do'] : '');
$postDo = (isset($_POST['do']) ? $_POST['do'] : '');

$tmp_dir = dirname($_SERVER['SCRIPT_FILENAME']);
if(DIRECTORY_SEPARATOR==='\\') $tmp_dir = str_replace('/',DIRECTORY_SEPARATOR,$tmp_dir);
$tmp = get_absolute_path($tmp_dir . '/' .$requestFile);



if($tmp === false)
	err(404,'File or Directory Not Found');
if(substr($tmp, 0,strlen($tmp_dir)) !== $tmp_dir)
	err(403,"Forbidden");
if(strpos($requestFile, DIRECTORY_SEPARATOR) === 0)
	err(403,"Forbidden");
if(preg_match('@^.+://@',$requestFile)) {
	err(403,"Forbidden");
}


if(!isset($_COOKIE['_sfm_xsrf']))
	setcookie('_sfm_xsrf',bin2hex(openssl_random_pseudo_bytes(16)));
if($_POST) {
	if(isset($_COOKIE['_sfm_xsrf']) && $_COOKIE['_sfm_xsrf'] !== $_POST['xsrf'] || !$_POST['xsrf'])
		err(403,"XSRF Failure");
}

$file = $requestFile ?: '/mnt/sda3/Library/Relaxation';


if($getDo == 'list') {
	if (is_dir($file)) {
		$directory = $file;
		$result = [];
		$files = array_diff(scandir($directory), ['.','..']);
		foreach ($files as $entry) if (!is_entry_ignored($entry, $allow_show_folders, $hidden_patterns)) {
			if($entry == 'lost+found')continue;
			$i = $directory . '/' . $entry;
			$is_dir = is_dir($i);			
		
			if(!$is_dir){
				$ext = pathinfo($i)['extension'];
				if(!in_array($ext, $video_extensions))continue;
				//$file_meta = $getID3->analyze($i);
				if(isset($file_meta['playtime_seconds']))$seconds = intval($file_meta['playtime_seconds']);
			}		
			
			$result[] = [

				'name' => basename($i),
				'path' => preg_replace('@^\./@', '', $i),
				'is_dir' => $is_dir,
				'is_deleteable' => $allow_delete && ((!is_dir($i) && is_writable($directory)) ||
														(is_dir($i) && is_writable($directory) && is_recursively_deleteable($i))),

				'length' => (isset($file_meta['playtime_string']) ? $file_meta['playtime_string'] : ''),
				'seconds' => (isset($file_meta['playtime_seconds']) ? $file_meta['playtime_seconds'] : ''),
			];
		}
		usort($result,function($f1,$f2){
			$f1_key = ($f1['is_dir']?:2) . $f1['name'];
			$f2_key = ($f2['is_dir']?:2) . $f2['name'];
			return $f1_key > $f2_key;
		});
	} else {
		err(412,"Not a Directory");
	}
	echo json_encode(['success' => true, 'is_writable' => is_writable($file), 'results' =>$result]);
	exit;
} elseif ($postDo == 'delete') {
	if($allow_delete) {
		rmrf($file);
	}
	exit;
} elseif ($postDo == 'save') {	
	file_put_contents('playlist.txt',json_encode(($_POST['files'] ? $_POST['files'] : [])));
	unlink('playlist.mpv');

	$xml = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8"?><playlist></playlist>');
	$trackList = $xml->addChild('trackList');
	foreach ($_POST['files'] as $video) {
		$track = $trackList->addChild('track');
		$track->addChild('location', 'file://'.htmlspecialchars($video['path'], ENT_XML1 | ENT_QUOTES, 'UTF-8'));//.$tmp_dir.'/'
		$track->addChild('title', htmlspecialchars($video['name'], ENT_XML1 | ENT_QUOTES, 'UTF-8'));
		
		file_put_contents('playlist.mpv','file://'.$tmp_dir.'/'.$video['path'].PHP_EOL, FILE_APPEND);
	}
	file_put_contents('playlist.xspf',$xml->asXML());
	echo json_encode(['success' => true]);
	
	exit;
} elseif ($postDo == 'mkdir' && $allow_create_folder) {
	// don't allow actions outside root. we also filter out slashes to catch args like './../outside'
	$dir = $_POST['name'];
	$dir = str_replace('/', '', $dir);
	if(substr($dir, 0, 2) === '..')
	    exit;
	chdir($file);
	@mkdir($_POST['name']);
	exit;
} elseif ($postDo == 'upload' && $allow_upload) {
	foreach($disallowed_patterns as $pattern)
		if(fnmatch($pattern, $_FILES['file_data']['name']))
			err(403,"Files of this type are not allowed.");

	$res = move_uploaded_file($_FILES['file_data']['tmp_name'], $file.'/'.$_FILES['file_data']['name']);
	exit;
} elseif ($getDo == 'download') {
	foreach($disallowed_patterns as $pattern)
		if(fnmatch($pattern, $file))
			err(403,"Files of this type are not allowed.");

	$filename = basename($file);
	$finfo = finfo_open(FILEINFO_MIME_TYPE);
	header('Content-Type: ' . finfo_file($finfo, $file));
	header('Content-Length: '. filesize($file));
	header(sprintf('Content-Disposition: attachment; filename=%s',
		strpos('MSIE',$_SERVER['HTTP_REFERER']) ? rawurlencode($filename) : "\"$filename\"" ));
	ob_flush();
	readfile($file);
	exit;
}

function is_entry_ignored($entry, $allow_show_folders, $hidden_patterns) {
	if ($entry === basename(__FILE__)) {
		return true;
	}

	if (is_dir($entry) && !$allow_show_folders) {
		return true;
	}
	foreach($hidden_patterns as $pattern) {
		if(fnmatch($pattern,$entry)) {
			return true;
		}
	}
	return false;
}

function rmrf($dir) {
	if(is_dir($dir)) {
		$files = array_diff(scandir($dir), ['.','..']);
		foreach ($files as $file)
			rmrf("$dir/$file");
		rmdir($dir);
	} else {
		unlink($dir);
	}
}
function is_recursively_deleteable($d) {
	$stack = [$d];
	while($dir = array_pop($stack)) {
		if(!is_readable($dir) || !is_writable($dir))
			return false;
		$files = array_diff(scandir($dir), ['.','..']);
		foreach($files as $file) if(is_dir($file)) {
			$stack[] = "$dir/$file";
		}
	}
	return true;
}

// from: http://php.net/manual/en/function.realpath.php#84012
function get_absolute_path($path) {
        $path = str_replace(['/', '\\'], DIRECTORY_SEPARATOR, $path);
        $parts = explode(DIRECTORY_SEPARATOR, $path);
        $absolutes = [];
        foreach ($parts as $part) {
            if ('.' == $part) continue;
            if ('..' == $part) {
                array_pop($absolutes);
            } else {
                $absolutes[] = $part;
            }
        }
        return implode(DIRECTORY_SEPARATOR, $absolutes);
    }

function err($code,$msg) {
	http_response_code($code);
	header("Content-Type: application/json");
	echo json_encode(['error' => ['code'=>intval($code), 'msg' => $msg]]);
	exit;
}

function asBytes($ini_v) {
	$ini_v = trim($ini_v);
	$s = ['g'=> 1<<30, 'm' => 1<<20, 'k' => 1<<10];
	return intval($ini_v) * ($s[strtolower(substr($ini_v,-1))] ?: 1);
}
$MAX_UPLOAD_SIZE = min(asBytes(ini_get('post_max_size')), asBytes(ini_get('upload_max_filesize')));
?>
<!DOCTYPE html>
<html><head>
<title>Channel <?php echo $channel; ?> TV Playlist</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8">

<style>
body {font-family: "lucida grande","Segoe UI",Arial, sans-serif; font-size: 14px;margin:0;}
th { color: #1F75CC; background-color: #F0F9FF; padding:.5em 1em .5em .2em;
	text-align: left;font-weight:bold;}
th .indicator {margin-left: 6px }
thead {border-top: 1px solid #82CFFA; border-bottom: 1px solid #96C4EA;	}
#top {height:52px;}
#mkdir {display:inline-block;float:right;padding-top:16px;}
label { display:block; font-size:11px; color:#555;}
#file_drop_target {width:250px; padding:12px 0; border: 4px dashed #ccc;font-size:12px;color:#ccc;
	text-align: center;float:right;margin-right:20px;}
#file_drop_target.drag_over {border: 4px dashed #96C4EA; color: #96C4EA;}
#upload_progress {padding: 4px 0;text-align:center;}
#upload_progress .error {color:#a00;}
#upload_progress > div { padding:3px 0;}
.no_write #mkdir, .no_write #file_drop_target {display: none}
.progress_track {display:inline-block;width:200px;height:10px;border:1px solid #333;margin: 0 4px 0 10px;}
.progress {background-color: #82CFFA;height:10px; }
footer {font-size:11px; color:#bbbbc5; padding:4em 0 0;text-align: left;}
footer a, footer a:visited {color:#bbbbc5;}
#breadcrumb { flex-grow:1; font-size:15px; color:#aaa;display:inline-block;float:left;}

#folder_actions {width: 50%;float:right;}
a, a:visited { color:#00c; text-decoration: none}
a:hover {text-decoration: underline}
.sort_hide{ display:none;}
table {border-collapse: collapse;width:100%;}

td { padding:.2em 1em .2em .2em; border-bottom:1px solid #def;height:30px; font-size:12px;white-space: nowrap;}
td.first {font-size:14px;white-space: normal;}
td.empty { color:#777; font-style: italic; text-align: center;}
.is_dir .size {color:transparent;font-size:0;}
.is_dir .size:before {content: "--"; font-size:14px;color:#333;}
.is_dir .download{visibility: hidden}


.is_dir .name {
	background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAADdgAAA3YBfdWCzAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAI0SURBVFiF7Vctb1RRED1nZu5977VQVBEQBKZ1GCDBEwy+ISgCBsMPwOH4CUXgsKQOAxq5CaKChEBqShNK222327f79n0MgpRQ2qC2twKOGjE352TO3Jl76e44S8iZsgOww+Dhi/V3nePOsQRFv679/qsnV96ehgAeWvBged3vXi+OJewMW/Q+T8YCLr18fPnNqQq4fS0/MWlQdviwVqNpp9Mvs7l8Wn50aRH4zQIAqOruxANZAG4thKmQA8D7j5OFw/iIgLXvo6mR/B36K+LNp71vVd1cTMR8BFmwTesc88/uLQ5FKO4+k4aarbuPnq98mbdo2q70hmU0VREkEeCOtqrbMprmFqM1psoYAsg0U9EBtB0YozUWzWpVZQgBxMm3YPoCiLpxRrPaYrBKRSUL5qn2AgFU0koMVlkMOo6G2SIymQCAGE/AGHRsWbCRKc8VmaBN4wBIwkZkFmxkWZDSFCwyommZSABgCmZBSsuiHahA8kA2iZYzSapAsmgHlgfdVyGLTFg3iZqQhAqZB923GGUgQhYRVElmAUXIGGVgedQ9AJJnAkqyClCEkkfdM1Pt13VHdxDpnof0jgxB+mYqO5PaCSDRIAbgDgdpKjtmwm13irsnq4ATdKeYcNvUZAt0dg5NVwEQFKrJlpn45lwh/LpbWdela4K5QsXEN61tytWr81l5YSY/n4wdQH84qjd2J6vEz+W0BOAGgLlE/AMAPQCv6e4gmWYC/QF3d/7zf8P/An4AWL/T1+B2nyIAAAAASUVORK5CYII=) no-repeat scroll 0px 10px;
	padding:15px 0 10px 40px;
}

#table .remove,#playlist .add,#playlist .delete{display:none;}
tr:hover{background:#e6e6e6;}
#totalTime{text-align:center;font-weight:bold;padding:5px;}
.is_file .name{background:none;padding:0;}
.name{word-break: break-all;}
tbody:after {
    content:" ";
    line-height:72px;
}
th:last-child{padding:0;width:20px;}
table,th{text-align:right;}
th:first-child,td:first-child{text-align:left;}
html,body{height:100%;}
body{display:flex;flex-direction:column;}
#header{padding: 5px;
    padding-bottom: 0;}
.actions a{margin:5px;display:inline-block}
</style>
<script src="/jquery-ui-1.12.1/external/jquery/jquery.js"></script>
<script src="/jquery-ui-1.12.1/jquery-ui.js"></script>
<link rel="stylesheet" href="/jquery-ui-1.12.1/jquery-ui.css">
<script>

$(function(){
	var XSRF = (document.cookie.match('(^|; )_sfm_xsrf=([^;]*)')||0)[2];
	var MAX_UPLOAD_SIZE = <?php echo $MAX_UPLOAD_SIZE ?>;
	var $tbody = $('#list');
	$(window).on('hashchange',list).trigger('hashchange');
	//$('#table').tablesorter();

	$("#distro").click(function(){
		var items = $("#list").find(".is_file");
		var target = $("#playlist tbody");
		
		if(target.children().length){
			var spacing = target.children().length / items.length;
			
			items.each(function(index, element){
				
				var targetPosition = Math.floor(index*spacing)+index;
				target.children()[targetPosition].after(element);	
		
			});
		}else target.append(items);
		updatePlaylist()		
		savePlaylist();
	});


	$("#playlist tbody" ).sortable({
      placeholder: "ui-state-highlight",
    // forceHelperSize: true,
      update: function( event, ui ) {updatePlaylist();savePlaylist()}
    }).disableSelection();;
    			
	$("#table tbody" ).sortable({
	  items: "> .is_file",
	  connectWith: "#playlist tbody",
      placeholder: "ui-state-highlight",
      /*remove: function (e, li) {
        li.item.clone().insertAfter(li.item);
        $(this).sortable('cancel');
        return li.item.clone();
    }*/
    }).disableSelection();;	



	$('#table').on('click','.delete',function(data) {
		if (window.confirm("This will delete this file ?")) {
			$.post("",{'do':'delete',file:$(this).attr('data-file'),xsrf:XSRF},function(response){
				
			},'json').always(function() {
				list();
			 });
		}	
		return false;
	});
	function sec2time(seconds) {
		var pad = function(num, size) { return ('000' + num).slice(size * -1); },
		days = Math.floor(seconds / 86400),
		hours = Math.floor((seconds - days * 86400)/3600),
		minutes = Math.floor((seconds - (days*86400)-(hours*3600))/60);

		return days + 'd ' + pad(hours, 2) + 'h ' + pad(minutes, 2)+'m';
	}	
	function updatePlaylist(){return;
		var sum = 0;
		var items = $('#playlist tbody tr');
		items.each(function(index){
			sum += $(this).find('.time').data('seconds');		
		});	
		$('#totalTime').html('Playlist Length: '+sec2time(sum) +' ('+items.length+' items)');		
	}
	
	function savePlaylist(){
		var files = [];
		$('#playlist tbody tr').each(function(index){
			var item = {
					path:$(this).find('.play').attr('href'),
					name:$(this).find('.name').text(),
					//length:$(this).find('.time').text(),
					//seconds:$(this).find('.time').data('seconds')//,
					//size:$(this).find('.size').text()
				};
			
			files.push(item);
		});
	
		$.post("",{'do':'save',files:files,xsrf:XSRF},function(response){
			console.log('save: '+response.success);
			if(!response.success)alert('error: save failed');
		},'json');
		
	}
<?php	
	if(file_exists('playlist.txt')){
		$playlist = file_get_contents('playlist.txt');
		echo "var playlist = JSON.parse('".addslashes($playlist)."');"; 
		?>
		$.each(playlist,function(k,v){
			$("#playlist tbody").append(renderFileRow(v));
		});		
		updatePlaylist();
		<?php
	}
?>	


	
/*	$('#table').on('click','.add',function(data) {
			var $row = $(this).closest("tr").clone();
			$row.appendTo("#playlist tbody");
			updatePlaylist();
			savePlaylist();
			return false;
	});*/
	
	$('#playlist').on('click','.remove',function(data) {
			$(this).closest("tr").remove();
			updatePlaylist();
			savePlaylist();
			return false;
	});
	

	$('#mkdir').submit(function(e) {
		var hashval = decodeURIComponent(window.location.hash.substr(1)),
			$dir = $(this).find('[name=name]');
		e.preventDefault();
		$dir.val().length && $.post('?',{'do':'mkdir',name:$dir.val(),xsrf:XSRF,file:hashval},function(data){
	
		},'json').always(function() {
				list();
			 });
		$dir.val('');
		return false;
	});
<?php if($allow_upload): ?>
	// file upload stuff
	$('#file_drop_target').on('dragover',function(){
		$(this).addClass('drag_over');
		return false;
	}).on('dragend',function(){
		$(this).removeClass('drag_over');
		return false;
	}).on('drop',function(e){
		e.preventDefault();
		var files = e.originalEvent.dataTransfer.files;
		$.each(files,function(k,file) {
			uploadFile(file);
		});
		$(this).removeClass('drag_over');
	});
	$('input[type=file]').change(function(e) {
		e.preventDefault();
		$.each(this.files,function(k,file) {
			uploadFile(file);
		});
		$(this).val("");
	});


	function uploadFile(file) {
		var folder = decodeURIComponent(window.location.hash.substr(1));

		if(file.size > MAX_UPLOAD_SIZE) {
			var $error_row = renderFileSizeErrorRow(file,folder);
			$('#upload_progress').append($error_row);
			window.setTimeout(function(){$error_row.fadeOut();},5000);
			return false;
		}

		var $row = renderFileUploadRow(file,folder);
		$('#upload_progress').append($row);
		var fd = new FormData();
		fd.append('file_data',file);
		fd.append('file',folder);
		fd.append('xsrf',XSRF);
		fd.append('do','upload');
		var xhr = new XMLHttpRequest();
		xhr.open('POST', '?');
		xhr.onload = function() {
			$row.remove();
    		list();
  		};
		xhr.upload.onprogress = function(e){
			if(e.lengthComputable) {
				$row.find('.progress').css('width',(e.loaded/e.total*100 | 0)+'%' );
			}
		};
	    xhr.send(fd);
	}
	function renderFileUploadRow(file,folder) {
		return $row = $('<div/>')
			.append( $('<span class="fileuploadname" />').text( (folder ? folder+'/':'')+file.name))
			.append( $('<div class="progress_track"><div class="progress"></div></div>')  )
			.append( $('<span class="size" />').text(formatFileSize(file.size)) )
	};
	function renderFileSizeErrorRow(file,folder) {
		return $row = $('<div class="error" />')
			.append( $('<span class="fileuploadname" />').text( 'Error: ' + (folder ? folder+'/':'')+file.name))
			.append( $('<span/>').html(' file size - <b>' + formatFileSize(file.size) + '</b>'
				+' exceeds max upload size of <b>' + formatFileSize(MAX_UPLOAD_SIZE) + '</b>')  );
	}
<?php endif; ?>
	function list() {
		var hashval = window.location.hash.substr(1);
		$tbody.empty().append("<tr style='background:none;'><td colspan='10' style='text-align:center'><img src='loading.gif' /></td></tr>");
		$.get('?do=list&file='+ hashval,function(data) {
			$tbody.empty();
			$('#breadcrumb').empty().html(renderBreadcrumbs(hashval));
			if(data.success) {
				$.each(data.results,function(k,v){
					$tbody.append(renderFileRow(v));
				});
				//!data.results.length && $tbody.append('<tr><td class="empty" colspan=5>This folder is empty</td></tr>')
				data.is_writable ? $('body').removeClass('no_write') : $('body').addClass('no_write');
			} else {
				console.warn(data.error.msg);
			}
			//$('#table').retablesort();
		},'json');
	}
	function renderFileRow(data) {
		//if(data.name == '@eaDir' || (!data.is_dir && !data.length))return;
		
		var $title = (data.is_dir ? $('<a />').attr('href', '#' + encodeURIComponent(data.path) ).text(data.name) : $('<span />').append(data.name)).attr('title',data.path);//'./' + 
		$title.addClass('name');

		var $play_link = $('<a target="_blank" href="#" />').attr('href',data.path).addClass('play').append("<img src='play.png' />");//'./' + 
		var $delete_link = $('<a href="#" />').attr('data-file',data.path).addClass('delete').append("<img src='remove.png' />");
		//var $add_link = $('<a href="#" />').addClass('add').text('add');
		var $remove_link = $('<a href="#" />').addClass('remove').append("<img src='remove.png' />");

		var $html = $('<tr />')
			.addClass(data.is_dir ? 'is_dir' : 'is_file')
			.append( $('<td class="first" />').append($title) )	
			//.append( $('<td class="time"/>').text(data.length ? data.length : '').attr('data-seconds',data.seconds))
			.append( $('<td class="actions"/>').append(!data.is_dir ? $play_link : '').append($remove_link).append( data.is_deleteable ? $delete_link : '') )
		return $html;
	}
	function renderBreadcrumbs(path) {
		var base = "",
			$html = $('<div/>');//.append( $('<a href=#>Home</a></div>') )
		$.each(path.split('%2F'),function(k,v){
			if(v) {
				var v_as_text = decodeURIComponent(v);
				$html.append( $('<span/>').text(' ▸ ') )
					.append( $('<a/>').attr('href','#'+base+v).text(v_as_text) );
				base += v + '%2F';
			}
		});
		return $html;
	}
	function formatTimestamp(unix_timestamp) {
		var m = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
		var d = new Date(unix_timestamp*1000);
		return [m[d.getMonth()],' ',d.getDate(),', ',d.getFullYear()," ",
			(d.getHours() % 12 || 12),":",(d.getMinutes() < 10 ? '0' : '')+d.getMinutes(),
			" ",d.getHours() >= 12 ? 'PM' : 'AM'].join('');
	}
	function formatFileSize(bytes) {
		if(typeof(bytes)=='number'){
			var s = ['bytes', 'KB','MB','GB','TB','PB','EB'];
			for(var pos = 0;bytes >= 1000; pos++,bytes /= 1024);
			var d = Math.round(bytes*10);
			return pos ? [parseInt(d/10),".",d%10," ",s[pos]].join('') : bytes + ' bytes';
		}else return bytes;
	}
})

</script>
</head><body>
<div id="header">

	<div id="top">
	  <div style="float:left;margin:0;">
	  <h2 style="margin:0;">Channel <?php echo $channel; ?> TV Playlist</h2>
	  <span style="">Drag & Drop. Changes take effect midnight. Playlist Loops. <a href="/playlist/VLCPortable_3.0.10.paf.exe">VLC Portable</a></span>
	</div>
   <?php if($allow_create_folder): ?>
	<form action="?" method="post" id="mkdir" />
		<label for=dirname>Create New Folder</label><input id=dirname type=text name=name value="" />
		<input style="width:70px;" type="submit" value="create" />
	</form>

   <?php endif; ?>

   <?php if($allow_upload): ?>

	<div id="file_drop_target">
		Drag Files Here To Upload
		<b>or</b>
		<input style="width:74px;" type="file" accept="video/*" multiple />
	</div>
   <?php endif; ?>

</div>
	<div id="upload_progress"></div>
	<div style="display:flex;">
		<div id="breadcrumb">&nbsp;</div>
		<div id="totalTime"></div>
	
	</div>
</div>
<div style="display:flex;overflow:auto">
	<div style="width:50%;overflow-y:scroll">
		<table id="table"><thead><tr>
			<th>Files Available - Disk Space: <?php echo  100-intval((disk_free_space("/mnt/sda3")/disk_total_space("/mnt/sda3"))*100).'% - '.intval(disk_free_space("/mnt/sda3")/1000000000).' GB';?></th>
			<!--<th>Size</th>-->
			<!--<th>Length</th>-->
			<!--<th>Modified</th>
			<th>Permissions</th>-->
			<th><button id="distro">~></button></th>
		</tr></thead><tbody id="list">

		</tbody></table>
	</div>

	<div style="width:50%;overflow-y:scroll">
		<table id="playlist">
		<thead><tr>
			<th>Files in Playlist</th>
			<!--<th>Size</th>-->
			<!--<th>Length</th>-->
			<!--<th>Modified</th>
			<th>Permissions</th>-->
			<th></th>
		</tr></thead>
		<tbody></tbody></table>
	</div>
</div>

</body></html>
