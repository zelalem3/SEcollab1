

var search = document.getElementById("search");


function change()
{

event.preventDefault();
var text = document.getElementById("text").value;
if (text == "")
{
event.preventDefault();
}
else{

 window.location.href = "http://127.0.0.1:5000/searchprofile/" + text;

}




}

search.addEventListener("click", change);
var text = document.getElementById("text");
text.addEventListener("keydown", call);
function call()
{
if (event.key === "Enter") {
    change();
  }}