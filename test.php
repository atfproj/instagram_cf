<?php

class InstagramProxyClient {
    private $proxy;
    private $proxyAuth;
    private $cookies;
    
    public function __construct($proxy, $username = null, $password = null) {
        $this->proxy = $proxy;
        if ($username && $password) {
            $this->proxyAuth = $username . ':' . $password;
        }
        $this->cookies = tempnam(sys_get_temp_dir(), 'insta_cookies_');
    }
    
    public function makeRequest($url, $method = 'GET', $data = []) {
        $ch = curl_init();
        
        $options = [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_PROXY => $this->proxy,
            CURLOPT_PROXYTYPE => CURLPROXY_HTTP,
            CURLOPT_USERAGENT => $this->getRandomUserAgent(),
            CURLOPT_COOKIEJAR => $this->cookies,
            CURLOPT_COOKIEFILE => $this->cookies,
            CURLOPT_HTTPHEADER => [
                'Accept: */*',
                'Accept-Language: en-US,en;q=0.5',
                'Accept-Encoding: gzip, deflate, br',
                'Connection: keep-alive',
                'Upgrade-Insecure-Requests: 1',
            ]
        ];
        
        if ($this->proxyAuth) {
            $options[CURLOPT_PROXYUSERPWD] = $this->proxyAuth;
        }
        
        if ($method === 'POST') {
            $options[CURLOPT_POST] = true;
            $options[CURLOPT_POSTFIELDS] = $data;
        }
        
        curl_setopt_array($ch, $options);
        
        $response = curl_exec($ch);
        $info = curl_getinfo($ch);
        
        if (curl_errno($ch)) {
            throw new Exception('CURL error: ' . curl_error($ch));
        }
        
        curl_close($ch);
        
        return [
            'response' => $response,
            'info' => $info
        ];
    }
    
    private function getRandomUserAgent() {
        $userAgents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ];
        
        return $userAgents[array_rand($userAgents)];
    }
    
    public function __destruct() {
        if (file_exists($this->cookies)) {
            unlink($this->cookies);
        }
    }
}

try {
    $client = new InstagramProxyClient('192.241.122.132:8000', 'hZEYrh', '8zfv7m');
    $result = $client->makeRequest('https://www.instagram.com/s_bezrukov');
    preg_match('/<script type="application\/ld\+json">(.*?)<\/script>/s', $result['response'], $matches);
    
    if (isset($matches[1])) {
        $profileData = json_decode($matches[1], true);
        print_r($profileData);
    }
    
} catch (Exception $e) {
    echo 'Ошибка: ' . $e->getMessage();
}
?>