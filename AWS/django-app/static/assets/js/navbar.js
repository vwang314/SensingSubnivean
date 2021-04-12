var authorname = document.currentScript.getAttribute('authorname');
var username = document.currentScript.getAttribute('username');
document.write("<!-- Main navbar -->");
document.write("	<div class=\"navbar navbar-inverse\">");
document.write("		<div class=\"navbar-header\">");
document.write("			<a class=\"navbar-brand\" href=\"\/\"><i class=\"icon-atom\"><\/i> Sensing the Subnivean<\/a>");
document.write("");
document.write("			<ul class=\"nav navbar-nav pull-right visible-xs-block\">");
document.write("				<li><a data-toggle=\"collapse\" data-target=\"#navbar-mobile\"><i class=\"icon-tree5\"><\/i><\/a><\/li>");
document.write("			<\/ul>");
document.write("		<\/div>");
document.write("");
document.write("		<div class=\"navbar-collapse collapse\" id=\"navbar-mobile\">");
document.write("			<ul class=\"nav navbar-nav\">");
document.write("				<li><a href=\"\/\"><i class=\"icon-home2 position-left\"><\/i> Dashboard<\/a><\/li>");
document.write("");
document.write("			<\/ul>");


document.write("			<ul class=\"nav navbar-nav navbar-right\">");



document.write("<li><span class=\"label bg-blue\" style=\"margin-top:14px;\"><i class=\"icon-user position-left\"></i>"+authorname+"</span><\/li>");

document.write("				<li class=\"dropdown dropdown-user\">");
document.write("					<a class=\"dropdown-toggle\" data-toggle=\"dropdown\">");
document.write("						<i class=\"caret\"><\/i>");
document.write("					<\/a>");
document.write("");
document.write("					<ul class=\"dropdown-menu dropdown-menu-right\">");
document.write("						<li><i class=\"icon-user\"><\/i>"+username+"<\/li>");
document.write("						<li class=\"divider\"><\/li>");
document.write("						<li><a href=\"\/cp\"><i class=\"icon-cog5\"><\/i> Change Password<\/a><\/li>");
document.write("						<li><a href=\"\/accounts\/logout\"><i class=\"icon-switch2\"><\/i> Logout<\/a><\/li>");
document.write("					<\/ul>");
document.write("				<\/li>");
document.write("			<\/ul>");
document.write("		<\/div>");
document.write("	<\/div>");
document.write("	<!-- \/main navbar -->");
