
 window.onload = function() {
            setTimeout(function() {
                document.getElementById('text-container').textContent = 'Page loaded!';
            }, 3);
        };

var followButtons = document.querySelectorAll(".follow");

followButtons.forEach(function(button) {
  var user_id = button.getAttribute("user-id");
  button.addEventListener("click", function() {

    fetch("http://127.0.0.1:5000/follow/" + user_id, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(function(response) {

        if (response.ok) {

           if(response.status == 200)
          {
           button.textContent = "Followed";
           }
           else if(response.status == 201)
           {
           button.textContent = "Follow";
           }
          return response.json();
        } else {
          throw new Error("Error: " + response.status);
        }
      })
      .then(function(data) {
        if (data && data.message) {
          console.log(data.message);
          if(response.status == 200)
          {
           button.textContent = "Followed";
           }
           else if(response.status == 400)
           {
           button.textContent = "Follow";
           }
        } else {
          throw new Error("Invalid response data");
        }
      })
      .catch(function(error) {
        console.error(error);
      });
  });
});
var following = document.querySelectorAll(".follow");

following.forEach(function(button)
{


var user_id = button.getAttribute("user-id");
 fetch("http://127.0.0.1:5000/checkfollowing/" + user_id, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(function(response) {

        if (response.ok) {

          return response.json();
        } else {
          throw new Error("Error: " + response.status);
        }
      })
      .then(function(data) {
        if (data && data.message) {
          console.log(data.message);
           button.textContent = "Following";
        } else {
          throw new Error("Invalid response data");
        }
      })
      .catch(function(error) {
        console.error(error);
      });


});


