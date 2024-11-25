var hidebyself = false;
var external_prefix = "http://quote.eastmoney.com/unify/r/";

var external_prefix_m = "https://wap.eastmoney.com/quote/stock/"; //0.300106.html
function mo(elm){
	//if (hidebyself == true)
	//	return;
	let isMobile = window.matchMedia("only screen and (max-width: 760px)").matches;
	if ( isMobile){
		$("#mobile").text("Moble")
	}
	else {
		$("#mobile").text("Notmoble")
		console.log("Not mobile")
	}
	codeid = elm.parentElement.id	
	var x = elm.parentElement.offsetLeft + 20;
	var y = elm.parentElement.offsetTop + 40;
	$('#popup').css({
		position: 'absolute',
		left: x,
		top: y,
	})
	$("#popup").show();
	img = elm.src;
	if(img.includes("/etf"))
	{
		var sloc = img.indexOf("/etf");
		var fileName = img.substr(sloc + 1);
		var components = fileName.split("_")
		console.log(fileName);
		var new_file = [components[0],components[1],"111.png"].join("_")
		img = img.replace(fileName,new_file);
	}
	$("img#currentimg")[0].src = img;
	
	var comp;
	var file = codeid + "_componentsx.json";
	$.getJSON("data/compj/" + file, function(json) {
		$("#swlist").children().remove();
		comp = json;
		names = comp.stock_name;
		codes = comp.stock_code;
		changepcts = comp.changepercent;
		for (i in names) { 
			//console.log("name:" + names[i]);
			var name = names[i];
			var code = codes[i];
			var changepct = changepcts[i];
			var code_link = "0." +  code;
			if (code.startsWith('6'))
				code_link = "1." + code;
			var whole_link = external_prefix + code_link;
			if (isMobile)
				whole_link = external_prefix_m + code_link + ".html";
			var bgcolor = lut(changepct);
			$("#swlist").append("<div class='ml-2 symbol_item' id='" + code + "'><a href='" + whole_link +
				"' target='_blank' style='background-color:"+ bgcolor + ";color:black'>" + name +"</a></div>");
		}
		$("#mark").text("");
		$("#mark").append("codeid-" +codeid);
		var halfsize = Object.keys(codes).length/2;
		$("#start").val(5);
		$("#start").attr("max",halfsize);
		$("#getListImg").off("click");
		$("#getListImg").click(
			function(e ){
				var start = $("#start").val();
				var count = $("#count").val();
				// var end = parseInt(start)+parseInt(count)+1;
				// var list_len = Object.keys(codes).length;
				// if( end > list_len)
				// 	end = list_len;
				// var code_sublist = codes;
				// var c_sublist_array = []; //= sublist.join(",")
				// for (i = start; i<end; i++)
				// 	c_sublist_array.push(code_sublist[i]);
				// var sublist_as_string = c_sublist_array.join(",")
				// console.log(`Retrieving info of id: ${codeid} ,st: ${start}, cnt: ${count}`);
				// console.log(`##list of interest:${sublist_as_string}`);
				var param = `?cd=${codeid}&st=${start}&cnt=${count}`;
				var win = window.open('stocksinsector'+param, '_blank');
					if (win) {
						win.focus();
					}
			}
		)
		console.log(lut(3.5));
	});
	console.log("mo called, code id:" + codeid);
	
	
}

function hide_popup(){
	$("#popup").hide();
	console.log("hide popup called");
}

function mout(){
	hidebyself = false; //reset
	console.log("mout called");
}

$("#popup").mouseleave(function() {
	hidebyself = true;
	$("#popup").hide();
	console.log("click self called");
});

$(".sector img").mouseover( function(){
	mo(this);
});


function lut(  pctg ){
	var list = {10:"#FE0000",9:"#FF1919",8:"#FF3333",7:"#FF4D4D",
		6:"#FF6666",5:"#FF7F7F",4:"#FF9999",3:"#FFB2B2",
		2:"#FFCCCC",1:"#FFE5E5",0:"#FFFFFF"};
	var list_g = {10:"#00FE00",9:"#19FF19",8:"#33FF33",7:"#4DFF4D",
		6:"#66FF66", 5:"#7FFF7F",4:"#99FF99",3:"#B2FFB2",
		2:"#CCFFCC",1:"#E5FFE5",0:"#FFFFFF"};
	if(pctg>10)
		pctg = 9.99;
	if(pctg<-10)
		pctg = -9.99
	var grade =  Math.floor( pctg + 0.5 )  ;
	if (pctg >= 0) {
		return list[grade];
	}
	else {
		//var grade =  Math.floor( pctg - 0.5 );
		grade = grade * (-1);
		return list_g[grade];
	}
}
