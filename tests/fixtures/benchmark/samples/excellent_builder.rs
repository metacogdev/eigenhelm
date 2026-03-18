use std::marker::PhantomData;

pub struct Missing;
pub struct Set;

pub struct RequestBuilder<UrlState, MethodState> {
    url: String,
    method: String,
    headers: Vec<(String, String)>,
    body: Option<String>,
    _state: PhantomData<(UrlState, MethodState)>,
}

impl RequestBuilder<Missing, Missing> {
    pub fn new() -> Self {
        Self {
            url: String::new(),
            method: String::new(),
            headers: Vec::new(),
            body: None,
            _state: PhantomData,
        }
    }
}

impl<M> RequestBuilder<Missing, M> {
    pub fn url(self, url: &str) -> RequestBuilder<Set, M> {
        RequestBuilder {
            url: url.to_owned(),
            method: self.method,
            headers: self.headers,
            body: self.body,
            _state: PhantomData,
        }
    }
}

impl<U> RequestBuilder<U, Missing> {
    pub fn method(self, method: &str) -> RequestBuilder<U, Set> {
        RequestBuilder {
            url: self.url,
            method: method.to_uppercase(),
            headers: self.headers,
            body: self.body,
            _state: PhantomData,
        }
    }
}

impl<U, M> RequestBuilder<U, M> {
    pub fn header(mut self, key: &str, value: &str) -> Self {
        self.headers.push((key.to_owned(), value.to_owned()));
        self
    }

    pub fn body(mut self, body: &str) -> Self {
        self.body = Some(body.to_owned());
        self
    }
}

pub struct Request {
    pub url: String,
    pub method: String,
    pub headers: Vec<(String, String)>,
    pub body: Option<String>,
}

impl RequestBuilder<Set, Set> {
    pub fn build(self) -> Request {
        Request {
            url: self.url,
            method: self.method,
            headers: self.headers,
            body: self.body,
        }
    }
}
