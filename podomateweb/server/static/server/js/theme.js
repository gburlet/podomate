jQuery(function ($) {
    'use strict';
    var $win = $(window);
    var $doc = $(document);

    /*============================================
     PAGE LOADER
     ==============================================*/
    $win.on('load', function () {
        $('#page-loader').fadeOut(500);
        $('.holder').fadeOut(500);
    });
    

    /*============================================
      menu
      ==============================================*/
    $('.head-search a').on('click', function () {
        $('.search-input').toggleClass("search-input-visible");
    });


    /*============================================
      table Check box
      ==============================================*/
    if ($('.custom-table').length) {
        $doc.on('change', 'table thead [type="checkbox"]', function (e) {
            var $table = $(e.target).closest('table'),
                $checked = $(e.target).is(':checked');
            $('tbody [type="checkbox"]', $table).prop('checked', $checked);
        });
    }

    /*============================================
    COUNTER
     ==============================================*/
    var count = $('.count');
    if (count.length) {
        count.counterUp({
            delay: 10,
            time: 1000
        });
    }
    /*============================================
      scrolling effect
      ==============================================*/
    if ($('.aos-box').length) {
        AOS.init();
    }

    /*============================================
      modals
      ==============================================*/

    if ($('.sweet-2').length) {
        $('.sweet-2').on('click', function () {
            swal('Any fool can use a computer')
        });
    }



    if ($('.sweet-3').length) {
        $('.sweet-3').on('click', function () {
            swal("Good job!", "You clicked the button!", "success");
        });
    }


    if ($('.sweet-4').length) {
        $('.sweet-4').on('click', function () {
            swal({
                    title: "Are you sure?",
                    text: "You will not be able to recover this imaginary file!",
                    type: "warning",
                    showCancelButton: true,
                    confirmButtonClass: 'btn-danger',
                    confirmButtonText: 'Yes, delete it!',
                    closeOnConfirm: false,
                    //closeOnCancel: false
                },
                function () {
                    swal("Deleted!", "Your imaginary file has been deleted!", "success");
                });
        });
    }


    if ($('.sweet-5').length) {
        $('.sweet-5').on('click', function () {
            swal({
                    title: "Are you sure?",
                    text: "You will not be able to recover this imaginary file!",
                    type: "warning",
                    showCancelButton: true,
                    confirmButtonClass: 'btn-danger',
                    confirmButtonText: 'Yes, delete it!',
                    cancelButtonText: "No, cancel plx!",
                    closeOnConfirm: false,
                    closeOnCancel: false
                },
                function (isConfirm) {
                    if (isConfirm) {
                        swal("Deleted!", "Your imaginary file has been deleted!", "success");
                    } else {
                        swal("Cancelled", "Your imaginary file is safe :)", "error");
                    }
                });
        });
    }



    if ($('.sweet-6').length) {
        $('.sweet-6').on('click', function () {
            swal({
                title: "Sweet!",
                text: "Here's a custom image.",
                imageUrl: 'images/icon-alert.jpg'
            });
        });
    }



    if ($('.sweet-7').length) {
        $('.sweet-7').on('click', function () {
            swal({
                title: "An input!",
                text: "Write something interesting:",
                type: "input",
                showCancelButton: true,
                closeOnConfirm: false,
                animation: "slide-from-top",
                inputPlaceholder: "Write something"
            }, function (inputValue) {
                if (inputValue === false) return false;
                if (inputValue === "") {
                    swal.showInputError("You need to write something!");
                    return false
                }
                swal("Nice!", "You wrote: " + inputValue, "success");
            });
        });
    }




    if ($('.sweet-8').length) {
        $('.sweet-8').on('click ', function () {
            swal({
                title: "Ajax request example",
                text: "Submit to run ajax request",
                type: "info",
                showCancelButton: true,
                closeOnConfirm: false,
                showLoaderOnConfirm: true
            }, function () {
                setTimeout(function () {
                    swal("Ajax request finished!");
                }, 2000);
            });
        });
    }


    /*============================================
      Progress Bar
      ==============================================*/
    if ($('.scroll-progress-bar').length) {
        $win.on('scroll', function () {
            var hT = $('.scroll-progress-bar').offset().top,
                hH = $('.scroll-progress-bar').outerHeight(),
                wH = $win.height(),
                wS = $(this).scrollTop();
            if (wS > (hT + hH - wH)) {
                $(function () {

                    $(".scroll-progress-bar > .progress > .progress-bar").each(function () {
                        var width = $(this).attr("aria-valuenow");
                        $(this).css("width", width + '%');
                    });

                });
            }
        });
    }

    /*============================================
      tab to accordian
      ==============================================*/
    if ($('.responsive-tabs').length) {
        var r_tabs = $('.responsive-tabs');
        r_tabs.responsiveTabs({
            accordionOn: ['xs'] // xs, sm, md, lg 
        });
    }
/*============================================
      match height
    ==============================================*/
    var equal_height = $(".equal-height");
        if (equal_height.length)
        {   
          equal_height.matchHeight();
        }

    /*============================================
      Swiper Slider
      ==============================================*/

    /*---------------------------------
      Swiper Carousal
      ---------------------------------*/
    if ($('.swiper-1').length) {
        var $swiper1 = new Swiper('.swiper-1', {
            autoplay: {
                delay: 3500,
                disableOnInteraction: false,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
        });
    }

    /*---------------------------------
      Swiper with Progress bar
      ---------------------------------*/
    if ($('.swiper-2').length) {
        var swiper2 = new Swiper('.swiper-2', {
            pagination: {
                el: '.swiper-pagination',
                type: 'progressbar',
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
        });
    }

    /*---------------------------------
      Swiper with Fraction Pagination
      ---------------------------------*/
    if ($('.swiper-3').length) {
        var swiper3 = new Swiper('.swiper-3', {
            pagination: {
                el: '.swiper-pagination',
                type: 'fraction',
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
        });
    }

    /*---------------------------------
      Vertical Swiper
      ---------------------------------*/
    if ($('.swiper-4').length) {
        var swiper4 = new Swiper('.swiper-4', {
                effect: 'cube',
                grabCursor: true,
                cubeEffect: {
                shadow: true,
                slideShadows: true,
                shadowOffset: 20,
                shadowScale: 0.94,
            },
                pagination: {
                el: '.swiper-pagination',
            },
        });
    }


    /*============================================
      Testimonial Section
      ==============================================*/

    /*---------------------------------
      Swiper Carousal
      ---------------------------------*/
    if ($('.testimonial_items').length) {
        $('.owl-carousel.testimonial_items').owlCarousel({
            loop: true,
            margin: 30,
            nav: true,
            navText: false,
            responsive: {
                0: {
                    items: 1
                },
                600: {
                    items: 3
                },
                1000: {
                    items: 3
                }
            }
        });
    }
    /*---------------------------------
      Swiper Carousal
      ---------------------------------*/
    if ($('.testimonial_single_items').length) {
        $('.owl-carousel.testimonial_single_items').owlCarousel({
            loop: true,
            margin: 30,
            autoplay: true,
            autoplayTimeout: 3000,
            autoplayHoverPause: false,
            nav: true,
            navText: false,
            items: 1
        })
    }


    /*============================================
      Client Section
      ==============================================*/
    if ($('.client-slider').length) {
        $('.owl-carousel.client-slider').owlCarousel({
            loop: true,
            margin: 0,
            autoplay: true,
            autoplayTimeout: 3000,
            autoplayHoverPause: false,
            smartSpeed: 2000,
            responsive: {
                0: {
                    items: 1
                },
                600: {
                    items: 3
                },
                1000: {
                    items: 5
                }
            }
        })

    }


    /*============================================
      Navigation Section
      ==============================================*/
    $win.on('scroll', function () {
        var scroll = $win.scrollTop();

        if (scroll) {
            $(".blank-menu").addClass("fixed-menu");
        } else {
            $(".blank-menu").removeClass("fixed-menu");
        }
    });

/*=============================================
  chat box
  ============================================*/
  if ($('#prime').length)
       {
         
       hideChat(0);
       
        var prime_id = $('#prime');
        var prime_cls = $('.prime');
        var chat = $('.chat');
        var fab = $('.fab');
        var prime_chat = $('#prime');
        var first_screen = $('#chat_first_screen');
        var second_screen = $('#chat_second_screen');
        var third_screen = $('#chat_third_screen');
        var fourth_screen = $('#chat_fourth_screen');
        var fullscreen_loader = $('#chat_fullscreen_loader');
        var header_img = $('.header_img');
        var img_container = $('.img_container');
        var chat_header = $('.chat_header');
        var fab_field = $('.fab_field');
        var fullscreen = $('.chat_fullscreen');

          prime_id.click(function() {
            toggleFab();
          });

//Toggle chat and links
function toggleFab() {
  prime_cls.toggleClass('zmdi-comment-outline');
  prime_cls.toggleClass('zmdi-close');
  prime_cls.toggleClass('is-active');
  prime_cls.toggleClass('is-visible');
  prime_id.toggleClass('is-float');
  chat.toggleClass('is-visible');
  fab.toggleClass('is-visible');
  
}

  first_screen.on('click', function(e) {
        hideChat(1);
  });

  second_screen.on('click', function(e) {
        hideChat(2);
  });

  third_screen.on('click', function(e) {
        hideChat(3);
  });

  fourth_screen.on('click', function(e) {
        hideChat(4);
  });

  fullscreen_loader.on('click', function(e) {
      fullscreen.toggleClass('zmdi-window-maximize');
      fullscreen.toggleClass('zmdi-window-restore');
      chat.toggleClass('chat_fullscreen');
      fab.toggleClass('is-hide');
      header_img.toggleClass('change_img');
      img_container.toggleClass('change_img');
      chat_header.toggleClass('chat_header2');
      fab_field.toggleClass('fab_field2');
      chat_converse.toggleClass('chat_converse2');
  });


function hideChat(hide) {

        var chat_converse = $('#chat_converse');
        var chat_body = $('#chat_body');
        var chat_form = $('#chat_form');
        var chat_login = $('.chat_login');
        var chat_fullscreen_loader = $('.chat_fullscreen_loader');
        var chat_fullscreen = $('#chat_fullscreen');

    switch (hide) {
      case 0:
            chat_converse.css('display', 'none');
            chat_body.css('display', 'none');
            chat_form.css('display', 'none');
            chat_login.css('display', 'block');
            chat_fullscreen_loader.css('display', 'none');
             chat_fullscreen.css('display', 'none');
            break;
      case 1:
            chat_converse.css('display', 'block');
            chat_body.css('display', 'none');
            chat_form.css('display', 'none');
            chat_login.css('display', 'none');
            chat_fullscreen_loader.css('display', 'block');
            break;
      case 2:
            chat_converse.css('display', 'none');
            chat_body.css('display', 'block');
            chat_form.css('display', 'none');
            chat_login.css('display', 'none');
            chat_fullscreen_loader.css('display', 'block');
            break;
      case 3:
            chat_converse.css('display', 'none');
            chat_body.css('display', 'none');
            chat_form.css('display', 'block');
            chat_login.css('display', 'none');
            chat_fullscreen_loader.css('display', 'block');
            break;
      case 4:
            chat_converse.css('display', 'none');
            chat_body.css('display', 'none');
            chat_form.css('display', 'none');
            chat_login.css('display', 'none');
            chat_fullscreen_loader.css('display', 'block');
            chat_fullscreen.css('display', 'block');
            break;
    }
}
}
    /*===========================================
      slider - banner -js
      =============================================*/
    /* Demo Scripts for Bootstrap Carousel and Animate.css article
     * on SitePoint by Maria Antonietta Perna
     */
    (function ($) {

        //Function to animate slider captions 
        function doAnimations(elems) {
            //Cache the animationend event in a variable
            var animEndEv = 'webkitAnimationEnd animationend';

            elems.each(function () {
                var $this = $(this),
                    $animationType = $this.data('animation');
                $this.addClass($animationType).one(animEndEv, function () {
                    $this.removeClass($animationType);
                });
            });
        }

        //Variables on page load 
        var $myCarousel = $('#carouselExampleIndicators'),
            $firstAnimatingElems = $myCarousel.find('.carousel-item:first').find("[data-animation ^= 'animated']");

        //Initialize carousel 
        $myCarousel.carousel();

        //Animate captions in first slide on page load 
        doAnimations($firstAnimatingElems);

        //Pause carousel  
        $myCarousel.carousel('pause');


        //Other slides to be animated on carousel slide event 
        $myCarousel.on('slide.bs.carousel', function (e) {
            var $animatingElems = $(e.relatedTarget).find("[data-animation ^= 'animated']");
            doAnimations($animatingElems);
        });

    })(jQuery);

});
