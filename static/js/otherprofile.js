

var button = document.getElementById("follow");


  var user_id = button.getAttribute("user-id");
  button.addEventListener("click", function() {

    fetch("http://100.25.23.191:5000/follow/" + user_id, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(function(response) {
        alert(response.status);
        if (response.ok) {

          button.textContent = "Followed";
          return response.json();
        } else {
          throw new Error("Error: " + response.status);
        }
      })
      .then(function(data) {
        if (data && data.message) {
          console.log(data.message);
           button.textContent = "Followed";
        } else {
          throw new Error("Invalid response data");
        }
      })
      .catch(function(error) {
        console.error(error);
      });
  });

