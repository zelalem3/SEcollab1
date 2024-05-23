var like = document.getElementById("like");
var blog_id = like.getAttribute("blog-id");
var blog_like = parseInt(like.getAttribute("blog-like"));
var isClicked = false;
var icon = document.getElementById("icon");

var numlike = document.getElementById("numlike");
var liked = numlike.getAttribute("liked");

if (liked == "None")
{
icon.style.color = "grey";

}
else{
icon.style.color = "blue";
}
numlike.textContent = blog_like;

like.addEventListener("click", function() {
    fetch("http://100.25.23.191:5000/addoremovelike/" + blog_id, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
    .then(function(response) {

     if (response.ok) {
    if (response.status == 201) {

            blog_like -= 1;
            icon.style.color = "grey";
            isClicked = false;

    } else if (response.status == 200) {

            blog_like += 1;
            icon.style.color = "blue";
            isClicked = true;

    }
    numlike.textContent = blog_like;
    return response.json();
} else {
    throw new Error("Error: " + response.status);
}

    })
    .then(function(data) {
        if (data && data.message) {
            // Handle message if needed
        } else {
            throw new Error("Invalid response data");
        }
    })
    .catch(function(error) {
        console.error(error);
    });
});
