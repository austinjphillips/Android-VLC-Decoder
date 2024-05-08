<!DOCTYPE html>
<html>
<head>
	<title>Message Change</title>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
</head>
<body>
	<?php
	session_start();
	$SysPassword="vlcs";
	


	if ($_SERVER["REQUEST_METHOD"] == "POST") {
			if (!isset($_SESSION["logged"]) || $_SESSION["logged"]==0){
				$password = $_POST["password"];
				if ($password == $SysPassword) {
					echo "<p>Login successful!</p>";
					$_SESSION["logged"]=1;
				} else {
					echo "<p>Invalid password. Please try again.</p>";
				}
			}else{
				$room_number=$_POST["number"];
				$room_text=$_POST["message"];
				if($room_number != ""){
					echo "Message Changed for Room ".$_POST["number"];
					$myfile = fopen("roommessages.json", "r") or die("Unable to open file!");
					$json_string = fread($myfile,filesize("roommessages.json"));
					fclose($myfile);

					$list_of_messages=json_decode($json_string, true);
					$list_of_messages[$room_number]=$room_text;
					$json_string=json_encode($list_of_messages);

					$myfile = fopen("roommessages.json", "w");
					fwrite($myfile,$json_string);
					fclose($myfile);
				}
			}
	}
	if (!isset($_SESSION["logged"])){
	echo "<form method='post' action=".htmlspecialchars($_SERVER["PHP_SELF"]).">
		<label for='password'>Password:</label><br>
		<input type='password' id='password' name='password'><br><br>
		<input type='submit' value='Submit'>
	</form>";
	}
	if (isset($_SESSION["logged"]) && $_SESSION["logged"]==1){

		$myfile = fopen("roommessages.json", "r") or die("Unable to open file!");
		$json_string = fread($myfile,filesize("roommessages.json"));
		fclose($myfile);
		$list_of_messages=json_decode($json_string, true);
		//var_dump($list_of_messages);
		echo "	<form method='post' action=".htmlspecialchars($_SERVER["PHP_SELF"]).">
				<label for='number'>Select a Room Number:</label>
				<select name='number' id='number'>";

		foreach($list_of_messages as $number=>$content){
			echo "<option value='".$number."'>".$number."</option>";
		}

		echo "	</select>

				<br><br>

				<label for='text'>Text (max. length 200 characters):</label>
				<input name='message' type='text' id='text' maxlength='200'  size='200'>
				<input type='submit' value='Submit'>
				</form>
				<script>
				$(document).ready(function() {
					var data = ".$json_string.";
					$('#number').change(function() {
						var number = $(this).val();
						var text = data[number];
						$('#text').val(text);
					});
					var number = $('#number').val();
					var text = data[number];
					$('#text').val(text);
					
				});

				$('#number').on('error', function() {
					console.log('Error: Unable to bind change event to #number element.');
				});
				
				</script>";		
	}
	?>
</body>
</html>
