var API_KEY = "b25b959554ed76058ac220b7b2e0a026"
var API_ROOT = "http://ws.audioscrobbler.com/2.0/?"

var onSubmit = function(event) {
    $('#loader').show()

    var params = $.param({
      method:      "track.gettoptags",
      artist:      $('#input-artist').val(),
      track:       $('#input-title').val(),
      autocorrect: 1,
      format:      "json",
      api_key:     API_KEY,
    });
    var url = API_ROOT + params;

    $.ajax(url).done(function(data) {
        $('#loader').hide();
        $('#input-artist').val(null);
        $('#input-title').val(null);
        try {
            var box = handleData(data);
            $('#boxes').prepend(box);
        } catch (ex) {
            alert(ex);
        }
    });
    return false;
}

var handleData = function(data) {
    var tags = data['toptags']['tag'];
    var artist = data['toptags']['@attr']['artist']
    var title = data['toptags']['@attr']['track']

    var box = $('#box-tpl').children(":first").clone()
    box.find('.artist').html(artist)
    box.find('.title').html(title)
    var container = box.children('.tags')
    for (var i = 0; i < tags.length; ++i) {
        elem = $('<span class="tag">' + tags[i]['name'] + '</span>');
        container.append(elem);
    }

    return box;
}

$(document).ready(function() {
    $('#userinput').submit(onSubmit);
});
