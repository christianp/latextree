$(document).ready(function(){
  $('.showhide').addClass("hidden");
  $('.showhide').click(function() {
    var $this = $(this);
    if ($this.hasClass("hidden")) {
      $(this).removeClass("hidden").addClass("visible");
  } else {
    $(this).removeClass("visible").addClass("hidden");
    }
  });
  $('.showhide_step').addClass("hidden");
  $('.showhide_step').hover(function() {
    var $this = $(this);
    if ($this.hasClass("hidden")) {
      $(this).removeClass("hidden").addClass("visible");
    } else {
      $(this).removeClass("visible").addClass("hidden");
    }
  });
});
