startRedirect = function(){
    if (location.search.search('redirectTo=') != -1){
        temp = location.search;
        temp = temp.substr(temp.search('redirectTo') + 11, temp.length);
        if (temp.search('&') != -1){
            temp = temp.substr(0, temp.search('&'));
        }
        location.href = unescape(temp);
    }
    tabbedview.view_container.unbind('reload', startRedirect);
} 

jq(function(){
    $ = jq;
    tabbedview.view_container.bind('reload', startRedirect);
});