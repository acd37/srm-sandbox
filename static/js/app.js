//Dismiss success alert
$(document).ready(function(){
  console.log('Timeout....')
  window.setTimeout(function(){
    $('#add-student-alert').alert('close'); }, 2000);
  });


function getStudent(clicked_id){
  var student_oid = clicked_id;
  window.location = "/student/" + student_oid
}

function getTask(clicked_id){
  var todo_id = clicked_id;
  window.location = "/delete_todo/" + todo_id
}


function getNote(clicked_id){
  var note_id = clicked_id;
  window.location = "/delete_note/" + note_id
}

$(document).ready(function(){
  $(".transfer-student:contains('no')").html('')
  $(".transfer-student:contains('None')").html('')
  $(".transfer-student:contains('yes')").html("<i class='fas fa-exchange-alt'></i>");
});

$(document).ready(function(){
  $(".direct-admit:contains('no')").html('')
  $(".direct-admit:contains('None')").html('')
  $(".direct-admit:contains('yes')").html("<i class='fas fa-star'></i>");
});

$("#new_codes_link").on("click", function(){
  $("#new_codes").fadeIn();
  $("#previous_codes").fadeOut();
});

$("#previous_codes_link").on("click", function(){
  $("#new_codes").fadeOut();
  $("#previous_codes").fadeIn();
})


function getStudents(){
  var settings = {
  "async": true,
  "crossDomain": true,
  "url": "http://localhost:5000/students",
  "method": "GET"
}

$.ajax(settings).done(function (response) {
  console.log(response);
});
}

function calculateGraduationTime(){
  var dateA = new Date($("#date_a").text());
  var dateB = new Date($("#date_b").text());
  var timeDiff = Math.abs(dateB.getTime() - dateA.getTime());
  var dateDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));
  var years = (dateDiff / 365).toFixed(2)

  console.log(dateDiff);
  console.log(years);

  $("#date_between").append(years + ' years')
};

$(document).ready(function(){
  calculateGraduationTime();
});
