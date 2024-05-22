var accepts = document.querySelectorAll(".accept");
accepts.forEach(function(accept) {
    accept.addEventListener("click", function() {
        var userid = accept.getAttribute("user-id");
        var project_id = accept.getAttribute("project-id");
        fetch("http://127.0.0.1:5000/accept/" + project_id + "/" + userid, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        })
        .then(function(response) {

            if (response.ok) {
                accept.textContent = "Added to the group";
                return response.json();
            } else {
                throw new Error("Error: " + response.status);
            }
        })
        .then(function(data) {
            if (data && data.message) {
                console.log(data.message);
            } else {
                throw new Error("Invalid response data");
            }
        })
        .catch(function(error) {
            console.error(error);
        });
    });
});
