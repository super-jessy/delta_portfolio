export default {
  multipass: true,
  plugins: [
    {
      name: "removeAttrs",
      params: {
        attrs: "(fill|stroke.*)"
      }
    }
  ]
};
