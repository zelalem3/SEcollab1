    var search = document.getElementById("search");
search.addEventListener("click", function()
{
event.preventDefault();
var text = document.getElementById("text").value;


 window.location.href = "http://100.25.23.191:5000/searchblog/" + text;


});
